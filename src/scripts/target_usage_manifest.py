from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

from amiga_reversing.disasm import c_backend
from src.scripts import amiga_hardware_usage
from src.scripts.platform_manifest_io import (
    ROOT,
    load_disk_image_bytes,
    read_jsonl_manifest,
    reconstruct_file_bytes,
    sha256,
    write_jsonl_manifest,
)

DEFAULT_DISK_MANIFEST = ROOT / "corpus" / "platform_disk_manifest.jsonl"
DEFAULT_FILE_MANIFEST = ROOT / "corpus" / "platform_file_manifest.jsonl"
DEFAULT_OUTPUT = ROOT / "corpus" / "target_usage_manifest.jsonl"
DEFAULT_XREF_OUTPUT = ROOT / "corpus" / "target_usage_xrefs.jsonl"
DEFAULT_SNIPPET_ROWS_OUTPUT = ROOT / "corpus" / "target_usage_snippet_rows.jsonl"
DEFAULT_VARIANT_OUTPUT = ROOT / "corpus" / "target_variant_index.jsonl"
DEFAULT_TYPE_FLOW_REPORT_OUTPUT = ROOT / "corpus" / "target_type_flow_report.jsonl"
DEFAULT_TYPE_FLOW_SNAPSHOT_DIR = ROOT / "corpus" / "type_flow_snapshots"
MAX_EXAMPLES = 5
CPU_NAMES = {
    0: "68000",
    1: "68010",
    2: "68020",
    3: "68030",
    4: "68040",
    5: "68060",
}
PLATFORM_EFFECT_NAMES = {
    1: "set_base_reg",
    2: "write_base_slot",
    3: "set_code_ptr_reg",
    4: "set_typed_reg",
    5: "write_typed_slot",
    6: "write_global_base_slot",
    7: "write_typed_global_slot",
}
FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "os": ("os_call", "os:"),
    "hardware": ("hardware:", "hardware_register:", "value_domain:amiga.custom", "value_domain:amiga.cia"),
    "devices": ("device:", "device_call"),
    "copper": ("data:copper_list", "hardware:custom/copper", "value_domain:amiga.custom.copper", "copper_register:"),
    "display": ("display:", "hardware:custom/display", "value_domain:amiga.custom.display_config"),
    "runtime": ("runtime:",),
    "app_slots": (
        "app_slot:",
        "app_slot_region:",
        "app_slot_region_source:",
        "app_slot_field_path:",
        "app_slot_field_gap:",
        "app_slot_field_gap_path:",
        "app_slot_base:",
        "app_slot_api_arg:",
        "app_slot_api_arg_reason:",
    ),
    "platform_types": (
        "platform_typed_access:",
        "platform_typed_access_struct:",
        "platform_typed_access_owner:",
        "platform_unresolved_typed_access:",
        "platform_unresolved_typed_access_struct:",
        "platform_field:",
        "platform_struct_field:",
        "platform_field_expr:",
        "typed_base_unresolved_field",
    ),
    "symbols": ("label:", "xref:label", "xref:segment"),
    "data": ("data:", "xref:data"),
    "diagnostics": ("diagnostic:",),
}


class FeatureBag:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.examples: dict[str, list[dict[str, object]]] = {}

    def add(self, key: str, count: int = 1, example: dict[str, object] | None = None) -> None:
        if not key or count <= 0:
            return
        self.counts[key] = self.counts.get(key, 0) + count
        if example is not None:
            items = self.examples.setdefault(key, [])
            if len(items) < MAX_EXAMPLES:
                items.append(_compact_example(example))

    def row_features(self) -> tuple[dict[str, int], dict[str, list[dict[str, object]]], list[str]]:
        counts = dict(sorted(self.counts.items()))
        examples = {key: self.examples[key] for key in sorted(self.examples) if key in counts}
        tags = sorted(counts)
        return counts, examples, tags


class DiskFileResolver:
    def __init__(self, disk_entries: list[dict[str, Any]], *, root: Path = ROOT) -> None:
        self.root = root
        self.by_id = {str(entry.get("id")): entry for entry in disk_entries if isinstance(entry.get("id"), str)}
        self.image_cache: dict[str, bytes] = {}

    def file_bytes(self, file_entry: dict[str, Any]) -> bytes:
        file_ref = file_entry.get("file_ref")
        origin = file_entry.get("origin")
        if not isinstance(file_ref, dict) or not isinstance(origin, dict):
            raise RuntimeError("File manifest row has no file_ref/origin")
        disk_id = file_ref.get("disk_id")
        image_path = origin.get("in_image_path")
        if not isinstance(disk_id, str) or not isinstance(image_path, str):
            raise RuntimeError("File manifest row has no disk_id/in_image_path")
        disk_entry = self.by_id.get(disk_id)
        if disk_entry is None:
            raise RuntimeError(f"Missing disk manifest row for {disk_id}")
        disk_platform = str(disk_entry.get("platform"))
        image_bytes = self.image_cache.get(disk_id)
        if image_bytes is None:
            disk_origin = disk_entry.get("origin")
            if not isinstance(disk_origin, dict):
                raise RuntimeError("Disk manifest row has no origin")
            image_bytes = load_disk_image_bytes(disk_origin, root=self.root)
            self.image_cache[disk_id] = image_bytes
        candidate = _find_disk_file_entry(disk_entry, image_path)
        return reconstruct_file_bytes(disk_platform, candidate, image_bytes)


def _safe_part(value: object) -> str:
    text = str(value).strip() if value is not None else "unknown"
    text = re.sub(r"\s+", "_", text)
    return text.replace("\\", "/")


def _status(entry: dict[str, Any]) -> str:
    expect = entry.get("expect")
    if isinstance(expect, dict) and isinstance(expect.get("status"), str):
        return str(expect["status"])
    if isinstance(entry.get("status"), str):
        return str(entry["status"])
    return "unknown"


def _origin_summary(entry: dict[str, Any]) -> dict[str, object]:
    origin = entry.get("origin")
    if not isinstance(origin, dict):
        return {}
    keys = ("display_name", "source_relpath", "container_relpath", "member_name", "in_image_path")
    return {
        key: origin[key]
        for key in keys
        if key in origin and (isinstance(origin.get(key), (str, int, float, bool)) or origin.get(key) is None)
    }


def _base_row(source_manifest: str, entry: dict[str, Any], bag: FeatureBag) -> dict[str, object]:
    source_id = str(entry.get("id", "unknown"))
    platform = str(entry.get("platform", "unknown"))
    status = _status(entry)
    bag.add(f"platform:{platform}")
    bag.add(f"status:{status}")
    counts, examples, tags = bag.row_features()
    return {
        "schema_version": 1,
        "id": f"{source_manifest}:{source_id}",
        "source_manifest": source_manifest,
        "source_id": source_id,
        "platform": platform,
        "sha256": entry.get("sha256") if isinstance(entry.get("sha256"), str) else None,
        "size": entry.get("size") if isinstance(entry.get("size"), int) else None,
        "status": status,
        "origin": _origin_summary(entry),
        "feature_counts": counts,
        "feature_examples": examples,
        "tags": tags,
    }


def build_usage_manifest(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
) -> list[dict[str, object]]:
    rows, _xrefs = build_usage_catalog(disk_manifest_path, file_manifest_path, root=root)
    return rows


def build_usage_catalog(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows, xrefs, _snippet_rows = build_usage_outputs(disk_manifest_path, file_manifest_path, root=root)
    return rows, xrefs


def build_usage_outputs(
    disk_manifest_path: Path = DEFAULT_DISK_MANIFEST,
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
    *,
    root: Path = ROOT,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    disk_entries = read_jsonl_manifest(disk_manifest_path)
    file_entries = read_jsonl_manifest(file_manifest_path)
    resolver = DiskFileResolver(disk_entries, root=root)
    rows: list[dict[str, object]] = []
    xrefs: list[dict[str, object]] = []
    snippet_rows: list[dict[str, object]] = []
    for entry in disk_entries:
        row = _collect_disk_usage_row(entry)
        rows.append(row)
        xrefs.extend(_disk_usage_xrefs(row, entry))
    build_dir = root / "src" / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build_dir) as tmp:
        tmp_dir = Path(tmp)
        for entry in file_entries:
            row, row_xrefs, row_snippets = collect_file_usage_catalog_entry(entry, resolver, tmp_dir, root=root)
            rows.append(row)
            xrefs.extend(row_xrefs)
            snippet_rows.extend(row_snippets)
    rows = sorted(rows, key=lambda row: str(row["id"]))
    xrefs = sorted(
        xrefs,
        key=lambda row: (
            str(row.get("target_id")),
            str(row.get("feature")),
            _sort_int(row.get("section")),
            _sort_int(row.get("offset")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )
    snippet_rows = sorted(
        snippet_rows,
        key=lambda row: (
            str(row.get("target_id")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )
    return rows, xrefs, snippet_rows


def build_variant_index(
    file_manifest_path: Path = DEFAULT_FILE_MANIFEST,
) -> list[dict[str, object]]:
    groups: dict[tuple[str, str, str], dict[str, tuple[dict[str, Any], dict[str, Any]]]] = {}
    for entry in read_jsonl_manifest(file_manifest_path):
        platform = _string_value(entry.get("platform"))
        source_id = _string_value(entry.get("id"))
        if not platform or not source_id:
            continue
        for origin in _variant_origins(entry):
            in_image_path = _string_value(origin.get("in_image_path"))
            if not in_image_path:
                continue
            key = (
                platform,
                _disk_title_family(origin),
                _normalise_variant_path(in_image_path),
            )
            groups.setdefault(key, {}).setdefault(source_id, (entry, origin))

    rows: list[dict[str, object]] = []
    for (platform, title_family, file_path_key), members_by_id in sorted(groups.items()):
        members = list(members_by_id.values())
        entries = [entry for entry, _origin in members]
        hashes = sorted({str(entry.get("sha256")) for entry in entries if isinstance(entry.get("sha256"), str)})
        if len(hashes) <= 1:
            continue
        targets = [
            _variant_target(entry, origin)
            for entry, origin in sorted(members, key=_variant_member_sort_key)
        ]
        raw_id = json.dumps(
            {"platform": platform, "title_family": title_family, "file_path_key": file_path_key},
            sort_keys=True,
            separators=(",", ":"),
        )
        rows.append(
            {
                "schema_version": 1,
                "id": f"variant/{hashlib.sha256(raw_id.encode('utf-8')).hexdigest()[:20]}",
                "platform": platform,
                "title_family": title_family,
                "file_path_key": file_path_key,
                "display_path": _display_variant_path(members[0][1]),
                "target_count": len(targets),
                "unique_hash_count": len(hashes),
                "targets": targets,
            }
        )
    return rows


def _variant_origins(entry: dict[str, Any]) -> list[dict[str, Any]]:
    origin = entry.get("origin")
    if not isinstance(origin, dict):
        return []
    origins = [origin]
    alternate_origins = origin.get("alternate_origins")
    if isinstance(alternate_origins, list):
        origins.extend(item for item in alternate_origins if isinstance(item, dict))
    return origins


def _variant_target(entry: dict[str, Any], origin: dict[str, Any]) -> dict[str, object]:
    primary_origin = entry.get("origin") if isinstance(entry.get("origin"), dict) else {}
    file_ref = entry.get("file_ref") if isinstance(entry.get("file_ref"), dict) else {}
    alternate_origins = primary_origin.get("alternate_origins")
    return {
        "target_id": f"platform_file_manifest:{entry.get('id')}",
        "source_id": entry.get("id"),
        "platform": entry.get("platform"),
        "sha256": entry.get("sha256"),
        "size": entry.get("size"),
        "status": _status(entry),
        "origin": _origin_summary_from_origin(origin),
        "disk_id": file_ref.get("disk_id"),
        "disk_sha256": entry.get("disk_sha256"),
        "origin_count": 1 + (len(alternate_origins) if isinstance(alternate_origins, list) else 0),
    }


def _origin_summary_from_origin(origin: dict[str, Any]) -> dict[str, object]:
    keys = ("display_name", "source_relpath", "container_relpath", "member_name", "in_image_path")
    return {
        key: origin[key]
        for key in keys
        if key in origin and (isinstance(origin.get(key), (str, int, float, bool)) or origin.get(key) is None)
    }


def _variant_member_sort_key(member: tuple[dict[str, Any], dict[str, Any]]) -> tuple[str, str, str]:
    entry, origin = member
    return (
        str(origin.get("display_name", "")),
        str(origin.get("in_image_path", "")),
        str(entry.get("sha256", "")),
    )


def _display_variant_path(origin: dict[str, Any]) -> str:
    path = origin.get("in_image_path")
    return str(path) if isinstance(path, str) else ""


def _normalise_variant_path(path: str) -> str:
    return re.sub(r"/+", "/", path.replace("\\", "/").casefold().strip())


def _disk_title_family(origin: dict[str, Any]) -> str:
    name = (
        _string_value(origin.get("member_name"))
        or _string_value(origin.get("display_name"))
        or _string_value(origin.get("source_relpath"))
        or "unknown"
    )
    stem = Path(name.replace("\\", "/")).name
    for suffix in (".zip", ".adf", ".adz", ".st"):
        if stem.casefold().endswith(suffix):
            stem = stem[: -len(suffix)]
    stem = re.sub(r"\[[^\]]*\]", " ", stem)
    stem = re.sub(r"\([^)]*\)", " ", stem)
    stem = re.sub(r"\bdisk\s+\d+\s+of\s+\d+\b", " ", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[^a-zA-Z0-9]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip().casefold()
    return stem or "unknown"


def collect_disk_usage_rows(disk_entries: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [_collect_disk_usage_row(entry) for entry in disk_entries]


def collect_file_usage_row(
    entry: dict[str, Any],
    resolver: DiskFileResolver | None,
    tmp_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, object]:
    row, _xrefs, _snippet_rows = collect_file_usage_catalog_entry(entry, resolver, tmp_dir, root=root)
    return row


def collect_file_usage_catalog_entry(
    entry: dict[str, Any],
    resolver: DiskFileResolver | None,
    tmp_dir: Path,
    *,
    root: Path = ROOT,
) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    bag = FeatureBag()
    _add_file_manifest_features(entry, bag)
    platform = str(entry.get("platform", "unknown"))
    combined: dict[str, Any] | None = None
    analysis_error: str | None = None
    if _status(entry) == "ok" and platform in {"amiga-hunk", "atari-st"}:
        try:
            if resolver is None:
                raise RuntimeError("No disk resolver supplied")
            file_bytes = resolver.file_bytes(entry)
            combined = analyze_executable_file(platform, file_bytes, tmp_dir, root=root)
            _add_executable_analysis_features(combined, bag, platform=platform, root=root)
        except Exception as exc:
            analysis_error = str(exc)
            bag.add("diagnostic:analysis_error", example={"message": str(exc)})
    row = _base_row("platform_file_manifest", entry, bag)
    xrefs = _file_usage_xrefs(row, entry, combined, analysis_error)
    return row, xrefs, _snippet_rows_for_xrefs(row, combined, xrefs)


def analyze_executable_file(platform: str, file_bytes: bytes, tmp_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    suffix = ".prg" if platform == "atari-st" else ".hunk"
    path = tmp_dir / f"usage_{platform.replace('-', '_')}_{sha256(file_bytes)[:12]}{suffix}"
    path.write_bytes(file_bytes)
    include_dir = _include_dir_for_platform(platform, root)
    combined_text = c_backend._platform_file_text(
        "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc",
        platform,
        str(path),
        "",
        str(include_dir),
        project_root=root,
    )
    payload = json.loads(combined_text)
    if not isinstance(payload, dict):
        raise RuntimeError("C backend returned non-object usage analysis")
    return payload


def _include_dir_for_platform(platform: str, root: Path) -> Path | str:
    if platform.startswith("amiga"):
        return root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    return ""


def _collect_disk_usage_row(entry: dict[str, Any]) -> dict[str, object]:
    bag = FeatureBag()
    platform = str(entry.get("platform", "unknown"))
    bag.add("format:disk_image")
    bag.add(f"disk_platform:{platform}")
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if isinstance(inspect, dict):
        entries = inspect.get("entries")
        if isinstance(entries, list):
            bag.add("disk:entry", len(entries))
            for item in entries:
                if not isinstance(item, dict):
                    continue
                if item.get("is_executable_candidate") == 1:
                    bag.add("disk:executable_candidate", example={"path": item.get("path")})
                kind = item.get("kind")
                if isinstance(kind, int):
                    bag.add(f"disk:entry_kind:{kind}")
        trackloader = inspect.get("trackloader_analysis")
        if isinstance(trackloader, dict):
            bag.add("disk:trackloader")
            tracks = trackloader.get("candidate_code_tracks")
            if isinstance(tracks, list):
                bag.add("disk:candidate_code_track", len(tracks))
        if inspect.get("bootblock") or inspect.get("bootblock_analysis") or inspect.get("boot_ascii_strings"):
            bag.add("disk:bootblock")
    if _status(entry) != "ok":
        bag.add("diagnostic:manifest_error")
    return _base_row("platform_disk_manifest", entry, bag)


def _add_file_manifest_features(entry: dict[str, Any], bag: FeatureBag) -> None:
    platform = str(entry.get("platform", "unknown"))
    bag.add(f"file_platform:{platform}")
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if _status(entry) != "ok":
        bag.add("diagnostic:manifest_error", example={"message": expect.get("error") if isinstance(expect, dict) else None})
        return
    if not isinstance(inspect, dict):
        return
    file_kind = inspect.get("file_kind")
    if isinstance(file_kind, str) and file_kind:
        bag.add(f"format:{_safe_part(file_kind)}")
    inspected_platform = inspect.get("platform")
    if isinstance(inspected_platform, str) and inspected_platform:
        bag.add(f"inspect_platform:{_safe_part(inspected_platform)}")
    form_type = inspect.get("form_type")
    if isinstance(form_type, str) and form_type:
        bag.add(f"format:iff:{_safe_part(form_type)}")
    for name, feature in (
        ("section_count", "section"),
        ("fixup_count", "relocation:fixup"),
        ("global_symbol_count", "symbol:global"),
        ("local_symbol_count", "symbol:local"),
        ("external_symbol_count", "symbol:external"),
    ):
        value = inspect.get(name)
        if isinstance(value, int) and value > 0:
            bag.add(feature, value)
    if inspect.get("resident") is not None:
        bag.add("amiga:resident")
    if inspect.get("library") is not None:
        bag.add("amiga:library")


def _add_executable_analysis_features(
    combined: dict[str, Any],
    bag: FeatureBag,
    *,
    platform: str,
    root: Path,
) -> None:
    analysis = combined.get("analysis")
    listing = combined.get("listing")
    profile = combined.get("profile")
    if isinstance(profile, dict):
        generation = profile.get("generation")
        if isinstance(generation, str) and generation:
            bag.add(f"analysis_generation:{_safe_part(generation)}")
    if isinstance(analysis, dict):
        bag.add("analysis:facts_v2")
        _add_analysis_features(analysis, bag)
    if isinstance(listing, dict):
        _add_listing_features(listing, bag)
    app_slot_analysis = _app_slot_layout_analysis(combined, platform=platform, root=root)
    if app_slot_analysis is not None:
        combined["app_slot_analysis"] = app_slot_analysis
        _add_app_slot_layout_features(app_slot_analysis, bag)


def _app_slot_layout_analysis(combined: dict[str, Any], *, platform: str, root: Path) -> dict[str, object] | None:
    listing = combined.get("listing")
    if not isinstance(listing, dict):
        return None
    app_slot_analysis = listing.get("app_slot_analysis")
    return app_slot_analysis if isinstance(app_slot_analysis, dict) else None


def _add_app_slot_layout_features(app_slot_analysis: dict[str, object], bag: FeatureBag) -> None:
    for region in _dict_items(app_slot_analysis.get("regions")):
        source = _string_value(region.get("source")) or "unknown"
        if not _is_generated_app_slot_region_source(source):
            continue
        struct_name = _string_value(region.get("struct_name")) or "unknown"
        example = {
            "symbol": region.get("symbol"),
            "offset": region.get("offset"),
            "end": region.get("end"),
            "struct_name": struct_name,
            "source": source,
        }
        bag.add("app_slot:typed_region", example=example)
        bag.add(f"app_slot_region:{_safe_part(struct_name)}", example=example)
        bag.add(f"app_slot_region_source:{_safe_part(source)}", example=example)
        field_refs = _dict_items(region.get("field_refs"))
        typed_field_refs = [field_ref for field_ref in field_refs if _string_value(field_ref.get("field_name"))]
        if typed_field_refs:
            bag.add("app_slot:typed_field_ref", len(typed_field_refs), example=example)
        for field_ref in typed_field_refs:
            field_example = {
                **example,
                "field_offset": field_ref.get("field_offset"),
                "field_name": field_ref.get("field_name"),
                "field_path": _field_path_text(struct_name, field_ref),
            }
            if field_ref.get("field_inherited") is True:
                bag.add("app_slot:inherited_field_ref", example=field_example)
            if field_ref.get("field_nested") is True:
                bag.add("app_slot:nested_field_ref", example=field_example)
            field_path = _field_path_text(struct_name, field_ref)
            if field_path:
                bag.add(f"app_slot_field_path:{_safe_part(field_path)}", example=field_example)
    for gap in _dict_items(app_slot_analysis.get("field_gaps")):
        coverage = _string_value(gap.get("coverage")) or "unknown"
        field_path = _field_path_text(_string_value(gap.get("struct_name")) or "unknown", gap)
        example = {
            "region_id": gap.get("region_id"),
            "start": gap.get("start"),
            "end": gap.get("end"),
            "size": gap.get("size"),
            "coverage": coverage,
            "field_path": field_path,
        }
        bag.add("app_slot:field_gap", example=example)
        bag.add(f"app_slot_field_gap:{_safe_part(coverage)}", example=example)
        if field_path:
            bag.add(f"app_slot_field_gap_path:{_safe_part(field_path)}", example=example)
    for gap in _dict_items(app_slot_analysis.get("gaps")):
        bag.add(
            "app_slot:gap",
            example={
                "start": gap.get("start"),
                "end": gap.get("end"),
                "size": gap.get("size"),
                "after": gap.get("after"),
                "before": gap.get("before"),
            },
        )
    for suggestion in _dict_items(app_slot_analysis.get("suggestions")):
        if suggestion.get("kind") != "app_slot_region":
            continue
        metadata = suggestion.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        struct_name = _string_value(metadata.get("struct_name")) or "unknown"
        bag.add(
            "app_slot:suggested_region",
            example={
                "symbol": metadata.get("symbol"),
                "offset": metadata.get("offset"),
                "size": metadata.get("size"),
                "struct_name": struct_name,
                "action": suggestion.get("action"),
            },
        )
    for arg in _dict_items(app_slot_analysis.get("untyped_api_args")):
        function_name = _string_value(arg.get("function")) or "unknown"
        reason = _string_value(arg.get("reason")) or "unknown"
        example = {
            "symbol": arg.get("symbol"),
            "offset": arg.get("displacement"),
            "function": function_name,
            "input_name": arg.get("input_name"),
            "register": arg.get("register"),
            "type_name": arg.get("type_name"),
            "reason": reason,
        }
        bag.add("app_slot:untyped_api_arg", example=example)
        bag.add(f"app_slot_api_arg:{_safe_part(function_name)}", example=example)
        bag.add(f"app_slot_api_arg_reason:{_safe_part(reason)}", example=example)


def _is_generated_app_slot_region_source(source: str) -> bool:
    return source == "platform_api_arg"


def _platform_typed_access_parts(access: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    root_struct = _string_value(access.get("root_struct_name"))
    owner_struct = _string_value(access.get("owner_struct_name"))
    field_name = _string_value(access.get("field_name"))
    field_expr = _string_value(access.get("field_expr"))
    return root_struct, owner_struct, field_name, field_expr


def _add_platform_typed_access_features(
    bag: FeatureBag,
    access: dict[str, Any],
    *,
    example: dict[str, object],
) -> None:
    root_struct, owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
    owner_for_feature = owner_struct or root_struct
    bag.add("platform_typed_access:any", example=example)
    if root_struct:
        bag.add(f"platform_typed_access_struct:{_safe_part(root_struct)}", example=example)
        bag.add(f"struct:{_safe_part(root_struct)}", example=example)
    if owner_struct:
        bag.add(f"platform_typed_access_owner:{_safe_part(owner_struct)}", example=example)
    if field_name:
        bag.add(f"platform_field:{_safe_part(field_name)}", example=example)
        if owner_for_feature:
            bag.add(f"platform_struct_field:{_safe_part(owner_for_feature)}.{_safe_part(field_name)}", example=example)
    if field_expr and owner_for_feature:
        bag.add(f"platform_field_expr:{_safe_part(owner_for_feature)}.{_safe_part(field_expr)}", example=example)
    if access.get("inherited") is True or access.get("inherited") == 1:
        bag.add("platform_typed_access:inherited", example=example)
    if access.get("nested") is True or access.get("nested") == 1:
        bag.add("platform_typed_access:nested", example=example)


def _add_platform_unresolved_typed_access_features(
    bag: FeatureBag,
    access: dict[str, Any],
    *,
    example: dict[str, object],
) -> None:
    root_struct = _string_value(access.get("root_struct_name"))
    bag.add("typed_base_unresolved_field", example=example)
    bag.add("platform_unresolved_typed_access:any", example=example)
    if root_struct:
        bag.add(f"platform_unresolved_typed_access_struct:{_safe_part(root_struct)}", example=example)
        bag.add(f"struct:{_safe_part(root_struct)}", example=example)


def _add_analysis_features(analysis: dict[str, Any], bag: FeatureBag) -> None:
    findings = analysis.get("findings")
    if isinstance(findings, dict):
        required_cpu = findings.get("required_cpu")
        if isinstance(required_cpu, int) and required_cpu in CPU_NAMES:
            bag.add(f"cpu:{CPU_NAMES[required_cpu]}")
        violation_count = findings.get("cpu_violation_count")
        if isinstance(violation_count, int) and violation_count > 0:
            bag.add("diagnostic:cpu_violation", violation_count)
    for section in _dict_items(analysis.get("sections")):
        section_index = _int_value(section.get("section_index"), 0)
        for call in _dict_items(section.get("recovered_platform_calls")):
            library = _string_value(call.get("library_name")) or _string_value(call.get("note_base_name")) or "unknown"
            function = (
                _string_value(call.get("function_name"))
                or _string_value(call.get("symbol_name"))
                or _string_value(call.get("note_symbol_name"))
                or "unknown"
            ).removeprefix("_LVO")
            example = _offset_example(section_index, call.get("offset"), f"{library}/{function}")
            bag.add("os_call:any", example=example)
            bag.add(f"os_call_library:{_safe_part(library)}", example=example)
            bag.add(f"os:{_safe_part(library)}/{_safe_part(function)}", example=example)
            bag.add(f"os_library:{_safe_part(library)}", example=example)
            for feature in _device_call_features(function, call):
                bag.add(feature, example=example)
            available_since = _string_value(call.get("available_since"))
            if available_since:
                bag.add(f"os_version:min:{_safe_part(available_since)}")
            for item in _dict_items(call.get("inputs")):
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                i_struct = _string_value(item.get("i_struct"))
                if i_struct:
                    bag.add(f"struct:{_safe_part(i_struct)}", example=example)
            for item in _dict_items(call.get("outputs")):
                for reg in _list_strings(item.get("regs")):
                    bag.add(f"os_call_output_reg:{_safe_part(reg)}", example=example)
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                o_struct = _string_value(item.get("o_struct"))
                if o_struct:
                    bag.add(f"struct:{_safe_part(o_struct)}", example=example)
        for effect in _dict_items(section.get("recovered_platform_effects")):
            effect_kind = _int_value(effect.get("kind"))
            effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
            base_name = _string_value(effect.get("base_name"))
            effect_example = _offset_example(section_index, effect.get("offset"), base_name or effect_kind_name)
            if effect_kind_name:
                bag.add(f"platform_effect:{effect_kind_name}", example=effect_example)
            if base_name:
                bag.add(f"platform_base:{_safe_part(base_name)}", example=effect_example)
                if effect_kind_name == "write_base_slot":
                    bag.add("app_slot:base_slot", example=effect_example)
                    bag.add(f"app_slot_base:{_safe_part(base_name)}", example=effect_example)
            semantic_kind = _string_value(effect.get("semantic_kind"))
            if semantic_kind:
                bag.add(f"semantic:{_safe_part(semantic_kind)}")
            value_domain = _string_value(effect.get("value_domain_name"))
            if value_domain:
                bag.add(f"value_domain:{_safe_part(value_domain)}")
            type_name = _string_value(effect.get("type_name"))
            if type_name:
                bag.add(f"type:{_safe_part(type_name)}")
        for ref in _dict_items(section.get("app_slot_refs")):
            access = _string_value(ref.get("access")) or "unknown"
            example = _offset_example(section_index, ref.get("offset"), _string_value(ref.get("displacement")))
            bag.add("app_slot:any", example=example)
            bag.add(f"app_slot:{_safe_part(access)}", example=example)
        for access in _dict_items(section.get("recovered_platform_typed_accesses")):
            _root_struct, _owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
            example = _offset_example(section_index, access.get("offset"), field_expr or field_name)
            _add_platform_typed_access_features(bag, access, example=example)
        for access in _dict_items(section.get("recovered_platform_unresolved_typed_accesses")):
            root_struct = _string_value(access.get("root_struct_name"))
            displacement = _int_value(access.get("displacement"))
            example = _offset_example(section_index, access.get("offset"), root_struct)
            if displacement is not None:
                example["displacement"] = displacement
            example["struct_size"] = _int_value(access.get("struct_size"))
            _add_platform_unresolved_typed_access_features(bag, access, example=example)
        for runtime_view in _dict_items(section.get("runtime_views")):
            storage = _int_value(runtime_view.get("storage_address"))
            runtime = _int_value(runtime_view.get("runtime_address"))
            kind = _int_value(runtime_view.get("kind"))
            bag.add("runtime:view", example=_offset_example(section_index, runtime_view.get("storage_offset"), runtime))
            if kind is not None:
                bag.add(f"runtime:view_kind:{kind}")
            if storage is not None and runtime is not None and storage != runtime:
                bag.add("runtime:copied_code")
        violation_count = _int_value(section.get("violation_count"), 0)
        if violation_count > 0:
            bag.add("diagnostic:analysis_violation", violation_count)
        indirect_count = _int_value(section.get("recovered_indirect_site_count"), 0)
        if indirect_count > 0:
            bag.add("analysis:indirect_site", indirect_count)
        string_ref_count = _int_value(section.get("recovered_string_ref_count"), 0)
        if string_ref_count > 0:
            bag.add("data:string_ref", string_ref_count)


def _add_listing_features(listing: dict[str, Any], bag: FeatureBag) -> None:
    for row_index, row in enumerate(_dict_items(listing.get("rows"))):
        text = _string_value(row.get("text")) or ""
        opcode_or_directive = (_string_value(row.get("opcode_or_directive")) or "").upper()
        is_equate = bool(re.search(r"(^|\s)EQU(\s|$)", text))
        section_index = _int_value(row.get("section_index"), -1)
        offset = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
        example = _offset_example(section_index, offset, text.strip()[:160])
        example["row_index"] = row_index
        if _listing_row_label_symbol(row):
            bag.add("label:any", example=example)
            bag.add("label:definition", example=example)
        data_class = _string_value(row.get("data_class"))
        row_hardware_group_features: set[str] = set()
        if data_class:
            bag.add(f"data:{_safe_part(data_class)}", example=example)
            if data_class == "copper_list":
                bag.add("hardware:custom", example=example)
                row_hardware_group_features.update(amiga_hardware_usage.group_features("_custom", "copper", copper_row=True))
        if not is_equate:
            for base in amiga_hardware_usage.HARDWARE_BASES:
                if base in text:
                    bag.add(f"hardware:{base.removeprefix('_')}", example=example)
            for base, symbol in amiga_hardware_usage.symbol_refs_from_listing_text(text, copper_row=bool(data_class == "copper_list")):
                bag.add(f"hardware_register:{_safe_part(symbol)}", example=example)
                row_hardware_group_features.update(amiga_hardware_usage.group_features(base, symbol, copper_row=bool(data_class == "copper_list")))
        for feature in sorted(row_hardware_group_features):
            bag.add(feature, example=example)
        for feature in amiga_hardware_usage.display_features_from_listing_text(
            text, copper_row=bool(data_class == "copper_list")
        ):
            bag.add(feature, example=example)
        for operand in _dict_items(row.get("operand_parts")):
            segment_addr = _int_value(operand.get("segment_addr"))
            if segment_addr is not None:
                bag.add("xref:segment_ref", example=example)
                bag.add("xref:data_ref" if row.get("kind") == "data" else "xref:code_ref", example=example)
            symbol = _operand_symbol(operand)
            if symbol:
                bag.add("label:reference", example=example)
            metadata = operand.get("metadata")
            if isinstance(metadata, dict):
                value_domain = _string_value(metadata.get("value_domain"))
                if value_domain:
                    bag.add(f"value_domain:{_safe_part(value_domain)}", example=example)
                semantic_kind = _string_value(metadata.get("semantic_kind"))
                if semantic_kind:
                    bag.add(f"semantic:{_safe_part(semantic_kind)}", example=example)
                type_name = _string_value(metadata.get("type_name"))
                if type_name:
                    bag.add(f"type:{_safe_part(type_name)}", example=example)
        for app_ref in _dict_items(row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            bag.add("app_slot:any", example=example)
            bag.add(f"app_slot:{_safe_part(access)}", example=example)
        for access in _dict_items(row.get("typed_accesses")):
            _add_platform_typed_access_features(bag, access, example=example)


def _disk_usage_xrefs(row: dict[str, object], entry: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    xrefs.append(_xref(row, "format:disk_image", "format", text="disk image"))
    xrefs.append(_xref(row, f"disk_platform:{_safe_part(entry.get('platform'))}", "format", text=str(entry.get("platform"))))
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if isinstance(inspect, dict):
        entries = inspect.get("entries")
        if isinstance(entries, list):
            for item in entries:
                if not isinstance(item, dict):
                    continue
                path = _string_value(item.get("path")) or ""
                xrefs.append(_xref(row, "disk:entry", "disk_entry", text=path, symbol=path))
                if item.get("is_executable_candidate") == 1:
                    xrefs.append(_xref(row, "disk:executable_candidate", "disk_entry", text=path, symbol=path))
                kind = item.get("kind")
                if isinstance(kind, int):
                    xrefs.append(_xref(row, f"disk:entry_kind:{kind}", "disk_entry", text=path, value=kind))
        trackloader = inspect.get("trackloader_analysis")
        if isinstance(trackloader, dict):
            xrefs.append(_xref(row, "disk:trackloader", "disk_trackloader", text="trackloader analysis"))
            tracks = trackloader.get("candidate_code_tracks")
            if isinstance(tracks, list):
                for track in tracks:
                    if isinstance(track, int):
                        xrefs.append(_xref(row, "disk:candidate_code_track", "disk_trackloader", value=track, text=f"track {track}"))
        if inspect.get("bootblock") or inspect.get("bootblock_analysis") or inspect.get("boot_ascii_strings"):
            xrefs.append(_xref(row, "disk:bootblock", "disk_bootblock", text="bootblock"))
    if _status(entry) != "ok":
        xrefs.append(_xref(row, "diagnostic:manifest_error", "diagnostic", text="manifest error"))
    return _dedupe_xrefs(xrefs)


def _file_usage_xrefs(
    row: dict[str, object],
    entry: dict[str, Any],
    combined: dict[str, Any] | None,
    analysis_error: str | None,
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    xrefs.extend(_file_manifest_xrefs(row, entry))
    if analysis_error is not None:
        xrefs.append(_xref(row, "diagnostic:analysis_error", "diagnostic", text=analysis_error))
    if combined is not None:
        analysis = combined.get("analysis")
        listing = combined.get("listing")
        profile = combined.get("profile")
        if isinstance(profile, dict):
            generation = _string_value(profile.get("generation"))
            if generation:
                xrefs.append(_xref(row, f"analysis_generation:{_safe_part(generation)}", "analysis_profile", text=generation))
        row_locations = _listing_row_locations(listing if isinstance(listing, dict) else None)
        if isinstance(analysis, dict):
            xrefs.append(_xref(row, "analysis:facts_v2", "analysis_profile", text="facts_v2"))
            xrefs.extend(_analysis_xrefs(row, analysis, row_locations))
        if isinstance(listing, dict):
            xrefs.extend(_listing_xrefs(row, listing))
        app_slot_analysis = combined.get("app_slot_analysis")
        if isinstance(app_slot_analysis, dict):
            xrefs.extend(_app_slot_layout_xrefs(row, app_slot_analysis))
    return _dedupe_xrefs(xrefs)


def _snippet_rows_for_xrefs(
    target_row: dict[str, object],
    combined: dict[str, Any] | None,
    xrefs: list[dict[str, object]],
    *,
    before: int = 20,
    after: int = 20,
) -> list[dict[str, object]]:
    if combined is None:
        return []
    listing = combined.get("listing")
    rows = listing.get("rows") if isinstance(listing, dict) else None
    if not isinstance(rows, list):
        return []
    wanted: set[int] = set()
    for xref in xrefs:
        row_index = xref.get("row_index")
        if not isinstance(row_index, int):
            continue
        for index in range(max(0, row_index - before), min(len(rows), row_index + after + 1)):
            wanted.add(index)
    result: list[dict[str, object]] = []
    target_id = str(target_row.get("id"))
    for row_index in sorted(wanted):
        row = rows[row_index]
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "schema_version": 1,
                "id": _stable_snippet_row_id(target_id, row_index, row),
                "target_id": target_id,
                "row_index": row_index,
                "row": _compact_listing_row(row),
            }
        )
    return result


def _compact_listing_row(row: dict[str, Any]) -> dict[str, object]:
    keys = (
        "row_id",
        "kind",
        "text",
        "stable_key",
        "section_index",
        "start_offset",
        "end_offset",
        "storage_address",
        "runtime_address",
        "runtime_view_id",
        "addr",
        "bytes",
        "label",
        "opcode_or_directive",
        "operand_parts",
        "operand_text",
        "comment_text",
        "data_class",
        "structured_data",
        "app_slot_refs",
        "typed_accesses",
    )
    return {key: row[key] for key in keys if key in row}


def _stable_snippet_row_id(target_id: str, row_index: int, row: dict[str, Any]) -> str:
    raw = json.dumps(
        {
            "target_id": target_id,
            "row_index": row_index,
            "stable_key": row.get("stable_key"),
            "text": row.get("text"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _file_manifest_xrefs(row: dict[str, object], entry: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    platform = str(entry.get("platform", "unknown"))
    xrefs.append(_xref(row, f"file_platform:{_safe_part(platform)}", "format", text=platform))
    expect = entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    if _status(entry) != "ok":
        message = expect.get("error") if isinstance(expect, dict) else None
        xrefs.append(_xref(row, "diagnostic:manifest_error", "diagnostic", text=str(message or "manifest error")))
        return xrefs
    if not isinstance(inspect, dict):
        return xrefs
    for key, prefix in (
        ("file_kind", "format"),
        ("platform", "inspect_platform"),
    ):
        value = _string_value(inspect.get(key))
        if value:
            xrefs.append(_xref(row, f"{prefix}:{_safe_part(value)}", "format", text=value))
    form_type = _string_value(inspect.get("form_type"))
    if form_type:
        xrefs.append(_xref(row, f"format:iff:{_safe_part(form_type)}", "format", text=form_type))
    for name, feature in (
        ("section_count", "section"),
        ("fixup_count", "relocation:fixup"),
        ("global_symbol_count", "symbol:global"),
        ("local_symbol_count", "symbol:local"),
        ("external_symbol_count", "symbol:external"),
    ):
        value = inspect.get(name)
        if isinstance(value, int) and value > 0:
            xrefs.append(_xref(row, feature, "format_count", value=value, text=name))
    if inspect.get("resident") is not None:
        xrefs.append(_xref(row, "amiga:resident", "format", text="resident"))
    if inspect.get("library") is not None:
        xrefs.append(_xref(row, "amiga:library", "format", text="library"))
    return xrefs


def _listing_row_locations(listing: dict[str, Any] | None) -> dict[tuple[int, int], tuple[int, str | None, str | None]]:
    if listing is None:
        return {}
    rows = listing.get("rows")
    if not isinstance(rows, list):
        return {}
    ranked: dict[tuple[int, int], tuple[int, int, str | None, str | None]] = {}
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        section_index = _int_value(row.get("section_index"))
        if section_index is None:
            continue
        rank = _listing_row_location_rank(row)
        stable_key = _string_value(row.get("stable_key"))
        text = (_string_value(row.get("text")) or "").strip()
        for key in ("start_offset", "addr", "storage_address"):
            offset = _int_value(row.get(key))
            if offset is None:
                continue
            location_key = (section_index, offset)
            existing = ranked.get(location_key)
            if existing is None or rank < existing[0]:
                ranked[location_key] = (rank, row_index, stable_key, text or None)
    return {key: (value[1], value[2], value[3]) for key, value in ranked.items()}


def _listing_row_location_rank(row: dict[str, Any]) -> int:
    kind = _string_value(row.get("kind"))
    if kind == "instruction":
        return 0
    if kind == "data":
        return 1
    if kind == "directive":
        return 2
    if kind == "label":
        return 3
    return 4


def _row_location(
    row_locations: dict[tuple[int, int], tuple[int, str | None, str | None]],
    section_index: int | None,
    offset: int | None,
) -> tuple[int | None, str | None, str | None]:
    if section_index is None or offset is None:
        return None, None, None
    return row_locations.get((section_index, offset), (None, None, None))


def _platform_typed_access_xrefs(
    target_row: dict[str, object],
    access: dict[str, Any],
    *,
    section_index: int | None,
    offset: int | None,
    row_index: int | None,
    stable_key: str | None,
    row_text: str | None,
) -> list[dict[str, object]]:
    root_struct, owner_struct, field_name, field_expr = _platform_typed_access_parts(access)
    owner_for_feature = owner_struct or root_struct
    text = row_text or field_expr or field_name or owner_for_feature or "typed platform access"
    field_offset = _int_value(access.get("field_offset"))
    xrefs = [
        _xref(
            target_row,
            "platform_typed_access:any",
            "platform_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=field_name,
            value=field_offset,
            text=text,
        )
    ]
    if root_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_typed_access_struct:{_safe_part(root_struct)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=field_offset,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                target_row,
                f"struct:{_safe_part(root_struct)}",
                "struct",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=field_offset,
                text=text,
            )
        )
    if owner_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_typed_access_owner:{_safe_part(owner_struct)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=owner_struct,
                value=field_offset,
                text=text,
            )
        )
    if field_name:
        xrefs.append(
            _xref(
                target_row,
                f"platform_field:{_safe_part(field_name)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
        if owner_for_feature:
            xrefs.append(
                _xref(
                    target_row,
                    f"platform_struct_field:{_safe_part(owner_for_feature)}.{_safe_part(field_name)}",
                    "platform_typed_access",
                    section=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    symbol=field_name,
                    value=field_offset,
                    text=text,
                )
            )
    if field_expr and owner_for_feature:
        xrefs.append(
            _xref(
                target_row,
                f"platform_field_expr:{_safe_part(owner_for_feature)}.{_safe_part(field_expr)}",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    if access.get("inherited") is True or access.get("inherited") == 1:
        xrefs.append(
            _xref(
                target_row,
                "platform_typed_access:inherited",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    if access.get("nested") is True or access.get("nested") == 1:
        xrefs.append(
            _xref(
                target_row,
                "platform_typed_access:nested",
                "platform_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=field_name,
                value=field_offset,
                text=text,
            )
        )
    return xrefs


def _platform_unresolved_typed_access_xrefs(
    target_row: dict[str, object],
    access: dict[str, Any],
    *,
    section_index: int | None,
    offset: int | None,
    row_index: int | None,
    stable_key: str | None,
    row_text: str | None,
) -> list[dict[str, object]]:
    root_struct = _string_value(access.get("root_struct_name"))
    displacement = _int_value(access.get("displacement"))
    text = row_text or root_struct or "unresolved typed platform access"
    xrefs = [
        _xref(
            target_row,
            "typed_base_unresolved_field",
            "platform_unresolved_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=root_struct,
            value=displacement,
            text=text,
        ),
        _xref(
            target_row,
            "platform_unresolved_typed_access:any",
            "platform_unresolved_typed_access",
            section=section_index,
            offset=offset,
            row_index=row_index,
            stable_key=stable_key,
            symbol=root_struct,
            value=displacement,
            text=text,
        ),
    ]
    if root_struct:
        xrefs.append(
            _xref(
                target_row,
                f"platform_unresolved_typed_access_struct:{_safe_part(root_struct)}",
                "platform_unresolved_typed_access",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=displacement,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                target_row,
                f"struct:{_safe_part(root_struct)}",
                "struct",
                section=section_index,
                offset=offset,
                row_index=row_index,
                stable_key=stable_key,
                symbol=root_struct,
                value=displacement,
                text=text,
            )
        )
    return xrefs


def _analysis_xrefs(
    row: dict[str, object],
    analysis: dict[str, Any],
    row_locations: dict[tuple[int, int], tuple[int, str | None, str | None]],
) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    findings = analysis.get("findings")
    if isinstance(findings, dict):
        required_cpu = findings.get("required_cpu")
        if isinstance(required_cpu, int) and required_cpu in CPU_NAMES:
            xrefs.append(_xref(row, f"cpu:{CPU_NAMES[required_cpu]}", "cpu_requirement", value=required_cpu, text=CPU_NAMES[required_cpu]))
        violation_count = findings.get("cpu_violation_count")
        if isinstance(violation_count, int) and violation_count > 0:
            for index in range(violation_count):
                xrefs.append(_xref(row, "diagnostic:cpu_violation", "diagnostic", value=index, text="CPU violation"))
    for section in _dict_items(analysis.get("sections")):
        section_index = _int_value(section.get("section_index"), 0)
        for call in _dict_items(section.get("recovered_platform_calls")):
            library = _string_value(call.get("library_name")) or _string_value(call.get("note_base_name")) or "unknown"
            function = (
                _string_value(call.get("function_name"))
                or _string_value(call.get("symbol_name"))
                or _string_value(call.get("note_symbol_name"))
                or "unknown"
            ).removeprefix("_LVO")
            offset = _int_value(call.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            text = row_text or f"{library}/{function}"
            resolution = _platform_call_resolution(call)
            xrefs.append(_xref(row, "os_call:any", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os_call_library:{_safe_part(library)}", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os:{_safe_part(library)}/{_safe_part(function)}", "os_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            for feature in _device_call_features(function, call):
                xrefs.append(_xref(row, feature, "device_call", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=library, text=text, resolution=resolution))
            xrefs.append(_xref(row, f"os_library:{_safe_part(library)}", "os_library", symbol=library, text=library))
            available_since = _string_value(call.get("available_since"))
            if available_since:
                xrefs.append(_xref(row, f"os_version:min:{_safe_part(available_since)}", "os_version", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=available_since, text=text, resolution=resolution))
            for item in _dict_items(call.get("inputs")):
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=value_domain, text=text, resolution=resolution))
                i_struct = _string_value(item.get("i_struct"))
                if i_struct:
                    xrefs.append(_xref(row, f"struct:{_safe_part(i_struct)}", "struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=i_struct, text=text, resolution=resolution))
            for item in _dict_items(call.get("outputs")):
                output_struct = _string_value(item.get("o_struct"))
                for reg in _list_strings(item.get("regs")):
                    xrefs.append(_xref(row, f"os_call_output_reg:{_safe_part(reg)}", "os_call_output", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=reg, text=text, resolution=resolution))
                    if output_struct:
                        xrefs.append(_xref(row, f"os_call_output_struct:{_safe_part(output_struct)}", "os_call_output_struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, access=reg, value=output_struct, text=text, resolution=resolution))
                value_domain = _string_value(item.get("value_domain"))
                if value_domain:
                    xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=value_domain, text=text, resolution=resolution))
                if output_struct:
                    xrefs.append(_xref(row, f"struct:{_safe_part(output_struct)}", "struct", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=function, value=output_struct, text=text, resolution=resolution))
        for effect in _dict_items(section.get("recovered_platform_effects")):
            offset = _int_value(effect.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            effect_kind = _int_value(effect.get("kind"))
            effect_kind_name = PLATFORM_EFFECT_NAMES.get(effect_kind) if effect_kind is not None else None
            base_name = _string_value(effect.get("base_name"))
            if effect_kind_name:
                xrefs.append(_xref(row, f"platform_effect:{effect_kind_name}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=effect_kind_name, text=row_text or effect_kind_name))
            if base_name:
                xrefs.append(_xref(row, f"platform_base:{_safe_part(base_name)}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, text=row_text or base_name))
                if effect_kind_name == "write_base_slot":
                    xrefs.append(_xref(row, "app_slot:base_slot", "app_slot_base_slot", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, value=_int_value(effect.get("displacement")), text=row_text or base_name))
                    xrefs.append(_xref(row, f"app_slot_base:{_safe_part(base_name)}", "app_slot_base_slot", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, value=_int_value(effect.get("displacement")), text=row_text or base_name))
            semantic_kind = _string_value(effect.get("semantic_kind"))
            if semantic_kind:
                xrefs.append(_xref(row, f"semantic:{_safe_part(semantic_kind)}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=semantic_kind, text=row_text or base_name or semantic_kind))
            value_domain = _string_value(effect.get("value_domain_name"))
            if value_domain:
                xrefs.append(_xref(row, f"value_domain:{_safe_part(value_domain)}", "value_domain", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=value_domain, text=row_text or base_name or value_domain))
            type_name = _string_value(effect.get("type_name"))
            if type_name:
                xrefs.append(_xref(row, f"type:{_safe_part(type_name)}", "type", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=type_name, text=row_text or base_name or type_name))
        for ref in _dict_items(section.get("app_slot_refs")):
            access = _string_value(ref.get("access")) or "unknown"
            offset = _int_value(ref.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            symbol = _string_value(ref.get("symbol")) or _app_slot_symbol(ref.get("displacement"))
            displacement = _int_value(ref.get("displacement"))
            xrefs.append(_xref(row, "app_slot:any", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=row_text or symbol or "app slot"))
            xrefs.append(_xref(row, f"app_slot:{_safe_part(access)}", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=row_text or symbol or "app slot"))
        for access in _dict_items(section.get("recovered_platform_typed_accesses")):
            offset = _int_value(access.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            xrefs.extend(
                _platform_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=row_text,
                )
            )
        for access in _dict_items(section.get("recovered_platform_unresolved_typed_accesses")):
            offset = _int_value(access.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            xrefs.extend(
                _platform_unresolved_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=offset,
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=row_text,
                )
            )
        for runtime_view in _dict_items(section.get("runtime_views")):
            storage = _int_value(runtime_view.get("storage_address"))
            runtime = _int_value(runtime_view.get("runtime_address"))
            kind = _int_value(runtime_view.get("kind"))
            storage_offset = _int_value(runtime_view.get("storage_offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, storage_offset)
            xrefs.append(_xref(row, "runtime:view", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or f"storage=${_hex_int(storage)} runtime=${_hex_int(runtime)}"))
            if kind is not None:
                xrefs.append(_xref(row, f"runtime:view_kind:{kind}", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=kind, text=row_text or f"runtime view kind {kind}"))
            if storage is not None and runtime is not None and storage != runtime:
                xrefs.append(_xref(row, "runtime:copied_code", "runtime_view", section=section_index, offset=storage_offset, row_index=row_index, stable_key=stable_key, value=runtime, text=row_text or f"copied code ${runtime:04X}"))
        violations = _dict_items(section.get("violations"))
        if violations:
            for index, violation in enumerate(violations):
                offset = _int_value(violation.get("offset"))
                row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
                message = _string_value(violation.get("message")) or "analysis violation"
                kind = _int_value(violation.get("kind"))
                xrefs.append(_xref(row, "diagnostic:analysis_violation", "diagnostic", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, value=kind if kind is not None else index, text=row_text or message))
        else:
            violation_count = _int_value(section.get("violation_count"), 0) or 0
            for index in range(violation_count):
                xrefs.append(_xref(row, "diagnostic:analysis_violation", "diagnostic", section=section_index, value=index, text="analysis violation"))
        for name, feature in (
            ("recovered_indirect_site_count", "analysis:indirect_site"),
            ("recovered_string_ref_count", "data:string_ref"),
        ):
            count = _int_value(section.get(name), 0) or 0
            for index in range(count):
                xrefs.append(_xref(row, feature, "analysis_count", section=section_index, value=index, text=name))
    return xrefs


def _listing_xrefs(row: dict[str, object], listing: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    for row_index, listing_row in enumerate(_dict_items(listing.get("rows"))):
        text = _string_value(listing_row.get("text")) or ""
        opcode_or_directive = (_string_value(listing_row.get("opcode_or_directive")) or "").upper()
        is_equate = bool(re.search(r"(^|\s)EQU(\s|$)", text))
        section_index = _int_value(listing_row.get("section_index"), -1)
        offset = listing_row.get("start_offset") if isinstance(listing_row.get("start_offset"), int) else listing_row.get("addr")
        stable_key = _string_value(listing_row.get("stable_key"))
        data_class = _string_value(listing_row.get("data_class"))
        seen_group_features: set[str] = set()
        label_symbol = _listing_row_label_symbol(listing_row)
        if label_symbol:
            xrefs.append(_xref(row, "label:any", "label_definition", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=label_symbol, text=text.strip()))
            xrefs.append(_xref(row, "label:definition", "label_definition", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=label_symbol, text=text.strip()))
        if data_class:
            xrefs.append(_xref(row, f"data:{_safe_part(data_class)}", "data_class", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=data_class, text=text.strip()))
            if data_class == "copper_list":
                xrefs.append(_xref(row, "hardware:custom", "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol="_custom", text=text.strip()))
                for feature in amiga_hardware_usage.group_features("_custom", "copper", copper_row=True):
                    if feature not in seen_group_features:
                        seen_group_features.add(feature)
                        xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol="copper", text=text.strip()))
        if not is_equate:
            for base in amiga_hardware_usage.HARDWARE_BASES:
                if base in text:
                    xrefs.append(_xref(row, f"hardware:{base.removeprefix('_')}", "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base, text=text.strip()))
            for base, symbol in amiga_hardware_usage.symbol_refs_from_listing_text(text, copper_row=bool(data_class == "copper_list")):
                xrefs.append(_xref(row, f"hardware_register:{_safe_part(symbol)}", "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=text.strip()))
                if data_class == "copper_list":
                    xrefs.append(_xref(row, f"copper_register:{_safe_part(symbol)}", "copper_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=text.strip()))
                for feature in amiga_hardware_usage.group_features(base, symbol, copper_row=bool(data_class == "copper_list")):
                    if feature not in seen_group_features:
                        seen_group_features.add(feature)
                        xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=text.strip()))
        for feature in amiga_hardware_usage.display_features_from_listing_text(
            text, copper_row=bool(data_class == "copper_list")
        ):
            xrefs.append(_xref(row, feature, "display_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, text=text.strip()))
        for operand in _dict_items(listing_row.get("operand_parts")):
            operand_text = _string_value(operand.get("text")) or text.strip()
            segment_addr = _int_value(operand.get("segment_addr"))
            symbol = _operand_symbol(operand)
            if symbol:
                xrefs.append(_xref(row, "label:reference", "label_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=text.strip()))
            if segment_addr is not None:
                ref_feature = "xref:data_ref" if listing_row.get("kind") == "data" else "xref:code_ref"
                xrefs.append(_xref(row, "xref:segment_ref", "segment_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=segment_addr, text=operand_text))
                xrefs.append(_xref(row, ref_feature, "segment_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=segment_addr, text=operand_text))
            metadata = operand.get("metadata")
            if isinstance(metadata, dict):
                for key, prefix, kind in (
                    ("value_domain", "value_domain", "value_domain"),
                    ("semantic_kind", "semantic", "semantic"),
                    ("type_name", "type", "type"),
                ):
                    value = _string_value(metadata.get(key))
                    if value:
                        xrefs.append(_xref(row, f"{prefix}:{_safe_part(value)}", kind, section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, value=value, text=text.strip()))
        for app_ref in _dict_items(listing_row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            symbol = _string_value(app_ref.get("symbol")) or _app_slot_symbol(app_ref.get("displacement"))
            displacement = _int_value(app_ref.get("displacement"))
            xrefs.append(_xref(row, "app_slot:any", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=text.strip()))
            xrefs.append(_xref(row, f"app_slot:{_safe_part(access)}", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=text.strip()))
        for access in _dict_items(listing_row.get("typed_accesses")):
            xrefs.extend(
                _platform_typed_access_xrefs(
                    row,
                    access,
                    section_index=section_index,
                    offset=_int_value(offset),
                    row_index=row_index,
                    stable_key=stable_key,
                    row_text=text.strip(),
                )
            )
    return xrefs


def _app_slot_layout_xrefs(row: dict[str, object], app_slot_analysis: dict[str, Any]) -> list[dict[str, object]]:
    xrefs: list[dict[str, object]] = []
    for region in _dict_items(app_slot_analysis.get("regions")):
        source = _string_value(region.get("source")) or "unknown"
        if not _is_generated_app_slot_region_source(source):
            continue
        struct_name = _string_value(region.get("struct_name")) or "unknown"
        symbol = _string_value(region.get("symbol"))
        offset = _int_value(region.get("offset"))
        evidence = _dict_items(region.get("evidence"))
        first_evidence = evidence[0] if evidence else {}
        row_index = _int_value(first_evidence.get("row_index"))
        section = _int_value(first_evidence.get("hunk_index"))
        text = f"{symbol or 'app slot'}: {struct_name}"
        xrefs.append(
            _xref(
                row,
                "app_slot:typed_region",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=struct_name,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                row,
                f"app_slot_region:{_safe_part(struct_name)}",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=struct_name,
                text=text,
            )
        )
        xrefs.append(
            _xref(
                row,
                f"app_slot_region_source:{_safe_part(source)}",
                "app_slot_region",
                section=section,
                offset=offset,
                row_index=row_index,
                symbol=symbol,
                value=source,
                text=text,
            )
        )
        for field_ref in _dict_items(region.get("field_refs")):
            field_symbol = _string_value(field_ref.get("symbol")) or symbol
            field_offset = _int_value(field_ref.get("field_offset"))
            field_name = _string_value(field_ref.get("field_name"))
            if not field_name:
                continue
            field_path = _field_path_text(struct_name, field_ref) or field_name
            refs = _dict_items(field_ref.get("refs"))
            first_ref = refs[0] if refs else {}
            field_xref = dict(
                section=section,
                offset=offset,
                row_index=_int_value(first_ref.get("row_index"), row_index),
                stable_key=_string_value(first_ref.get("stable_key")),
                symbol=field_symbol,
                value=field_offset,
                text=f"{field_path} in {struct_name}",
            )
            xrefs.append(_xref(row, "app_slot:typed_field_ref", "app_slot_field_ref", **field_xref))
            if field_ref.get("field_inherited") is True:
                xrefs.append(_xref(row, "app_slot:inherited_field_ref", "app_slot_field_ref", **field_xref))
            if field_ref.get("field_nested") is True:
                xrefs.append(_xref(row, "app_slot:nested_field_ref", "app_slot_field_ref", **field_xref))
            xrefs.append(
                _xref(row, f"app_slot_field_path:{_safe_part(field_path)}", "app_slot_field_ref", **field_xref)
            )
    for gap in _dict_items(app_slot_analysis.get("field_gaps")):
        start = _int_value(gap.get("start"))
        end = _int_value(gap.get("end"))
        size = _int_value(gap.get("size"))
        coverage = _string_value(gap.get("coverage")) or "unknown"
        field_path = _field_path_text(_string_value(gap.get("struct_name")) or "unknown", gap)
        text = (
            f"app slot field gap ${start:04X}-${end:04X} {coverage}"
            if start is not None and end is not None
            else "app slot field gap"
        )
        field_gap_xref = dict(offset=start, value=size, text=field_path or text)
        xrefs.append(_xref(row, "app_slot:field_gap", "app_slot_field_gap", **field_gap_xref))
        xrefs.append(_xref(row, f"app_slot_field_gap:{_safe_part(coverage)}", "app_slot_field_gap", **field_gap_xref))
        if field_path:
            xrefs.append(
                _xref(row, f"app_slot_field_gap_path:{_safe_part(field_path)}", "app_slot_field_gap", **field_gap_xref)
            )
    for gap in _dict_items(app_slot_analysis.get("gaps")):
        start = _int_value(gap.get("start"))
        end = _int_value(gap.get("end"))
        size = _int_value(gap.get("size"))
        text = f"app slot gap ${start:04X}-${end:04X}" if start is not None and end is not None else "app slot gap"
        xrefs.append(
            _xref(
                row,
                "app_slot:gap",
                "app_slot_gap",
                offset=start,
                value=size,
                text=text,
            )
        )
    for suggestion in _dict_items(app_slot_analysis.get("suggestions")):
        if suggestion.get("kind") != "app_slot_region":
            continue
        metadata = suggestion.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        symbol = _string_value(metadata.get("symbol"))
        offset = _int_value(metadata.get("offset"))
        struct_name = _string_value(metadata.get("struct_name")) or "unknown"
        evidence = _dict_items(suggestion.get("evidence"))
        first_evidence = evidence[0] if evidence else {}
        xrefs.append(
            _xref(
                row,
                "app_slot:suggested_region",
                "app_slot_suggestion",
                section=_int_value(first_evidence.get("hunk_index")),
                offset=offset,
                row_index=_int_value(first_evidence.get("row_index")),
                symbol=symbol,
                value=struct_name,
                text=_string_value(suggestion.get("summary")) or f"{symbol or 'app slot'}: {struct_name}",
            )
        )
    for arg in _dict_items(app_slot_analysis.get("untyped_api_args")):
        function_name = _string_value(arg.get("function")) or "unknown"
        reason = _string_value(arg.get("reason")) or "unknown"
        arg_xref = dict(
            section=_int_value(arg.get("hunk_index")),
            offset=_int_value(arg.get("addr")),
            row_index=_int_value(arg.get("row_index")),
            stable_key=_string_value(arg.get("stable_key")),
            source_stable_key=_string_value(arg.get("source_stable_key")),
            symbol=_string_value(arg.get("symbol")),
            value=_int_value(arg.get("displacement")),
            text=f"{arg.get('symbol') or 'app slot'} -> {function_name} {arg.get('register') or ''}".strip(),
        )
        xrefs.append(_xref(row, "app_slot:untyped_api_arg", "app_slot_api_arg", **arg_xref))
        xrefs.append(_xref(row, f"app_slot_api_arg:{_safe_part(function_name)}", "app_slot_api_arg", **arg_xref))
        xrefs.append(_xref(row, f"app_slot_api_arg_reason:{_safe_part(reason)}", "app_slot_api_arg", **arg_xref))
    return xrefs


def _xref(
    target_row: dict[str, object],
    feature: str,
    kind: str,
    *,
    section: object = None,
    offset: object = None,
    row_index: object = None,
    stable_key: str | None = None,
    symbol: str | None = None,
    access: str | None = None,
    value: object = None,
    text: str | None = None,
    resolution: str | None = None,
    source_stable_key: str | None = None,
) -> dict[str, object]:
    target_id = str(target_row.get("id"))
    payload: dict[str, object] = {
        "schema_version": 1,
        "target_id": target_id,
        "feature": feature,
        "kind": kind,
        "platform": target_row.get("platform"),
        "source_id": target_row.get("source_id"),
        "origin": target_row.get("origin"),
        "section": section if isinstance(section, (int, str)) else None,
        "offset": offset if isinstance(offset, int) else None,
        "row_index": row_index if isinstance(row_index, int) else None,
        "stable_key": stable_key,
        "symbol": symbol,
        "access": access,
        "resolution": resolution,
        "value": value if isinstance(value, (str, int, float, bool)) or value is None else str(value),
        "text": text or "",
    }
    if source_stable_key is not None:
        payload["source_stable_key"] = source_stable_key
    payload["id"] = _stable_xref_id(payload)
    return payload


def _stable_xref_id(payload: dict[str, object]) -> str:
    keys = (
        "target_id",
        "feature",
        "kind",
        "section",
        "offset",
        "row_index",
        "stable_key",
        "symbol",
        "access",
        "resolution",
        "value",
        "text",
    )
    if payload.get("source_stable_key") is not None:
        keys = (*keys[:7], "source_stable_key", *keys[7:])
    raw = json.dumps({key: payload.get(key) for key in keys}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _dedupe_xrefs(xrefs: list[dict[str, object]]) -> list[dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for xref in xrefs:
        result[str(xref["id"])] = xref
    return list(result.values())


def _platform_call_resolution(call: dict[str, Any]) -> str:
    note_kind = _int_value(call.get("note_kind"), 0) or 0
    if note_kind == 1:
        return "indexed_vector"
    if note_kind == 2:
        return "callback_field"
    if note_kind == 3:
        return "local_wrapper"
    if note_kind == 4:
        return "direct_os_call"
    if note_kind == 5:
        return "stack_cleanup"
    return "direct"


def _device_call_features(function: str, call: dict[str, Any] | None = None) -> list[str]:
    if function in {
        "AbortIO",
        "BeginIO",
        "CheckIO",
        "CloseDevice",
        "DoIO",
        "OpenDevice",
        "SendIO",
        "WaitIO",
    }:
        features = ["device_call:any", f"device_call_function:{_safe_part(function)}"]
        for device_name in _device_names_from_call(call):
            safe_device = _safe_part(device_name)
            features.append(f"device:{safe_device}")
            features.append(f"device_call:{safe_device}/{_safe_part(function)}")
        return features
    return []


def _device_names_from_call(call: dict[str, Any] | None) -> list[str]:
    if not isinstance(call, dict):
        return []
    candidates: list[str] = []
    for key in ("device_name", "device", "target_device", "resolved_device"):
        value = _string_value(call.get(key))
        if value:
            candidates.append(value)
    for item in _dict_items(call.get("inputs")):
        input_name = (_string_value(item.get("name")) or "").casefold()
        if "device" not in input_name and input_name not in {"name", "devname"}:
            continue
        for key in ("device_name", "string_value", "value_text", "constant_name", "symbol", "value"):
            value = _string_value(item.get(key))
            if value:
                candidates.append(value)
    result: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        value = candidate.strip().strip('"')
        if not value.endswith(".device"):
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _app_slot_symbol(displacement: object) -> str | None:
    if isinstance(displacement, int):
        return f"app_{displacement & 0xFFFF:04X}"
    return None


def _field_path_text(struct_name: str, item: dict[str, object]) -> str | None:
    parts = _string_list(item.get("field_path"))
    if parts:
        return ".".join([struct_name, *parts])
    field_name = _string_value(item.get("field_name"))
    if field_name:
        return f"{struct_name}.{field_name}"
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _listing_row_label_symbol(row: dict[str, Any]) -> str | None:
    label = _string_value(row.get("label"))
    if label:
        return label.rstrip(":").strip() or None
    text = (_string_value(row.get("text")) or "").strip()
    if text.endswith(":") and " " not in text and "\t" not in text:
        return text[:-1].strip() or None
    return None


def _operand_symbol(operand: dict[str, Any]) -> str | None:
    metadata = operand.get("metadata")
    if isinstance(metadata, dict):
        for key in ("symbol", "symbol_name", "label", "name"):
            value = _string_value(metadata.get(key))
            if value:
                return value.rstrip(":")
    text = _string_value(operand.get("text"))
    if not text:
        return None
    candidate = text.strip().split("+", 1)[0].split("(", 1)[0].split(",", 1)[0].strip()
    if not candidate or candidate.startswith("#") or candidate.startswith("$"):
        return None
    if re.match(r"^[A-Za-z_][A-Za-z0-9_$.]*$", candidate):
        return candidate.rstrip(":")
    return None


def _hex_int(value: int | None) -> str:
    return "?" if value is None else f"{value:04X}"


def _find_disk_file_entry(disk_entry: dict[str, Any], image_path: str) -> dict[str, Any]:
    expect = disk_entry.get("expect")
    inspect = expect.get("inspect") if isinstance(expect, dict) else None
    entries = inspect.get("entries") if isinstance(inspect, dict) else None
    if isinstance(entries, list):
        for entry in entries:
            if isinstance(entry, dict) and entry.get("path") == image_path:
                return entry
    raise RuntimeError(f"Missing disk file entry {image_path}")


def _dict_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _string_value(value: object) -> str | None:
    if isinstance(value, str) and value != "":
        return value
    if isinstance(value, int):
        return str(value)
    return None


def _int_value(value: object, default: int | None = None) -> int | None:
    return value if isinstance(value, int) else default


def _sort_int(value: object) -> int:
    return value if isinstance(value, int) else -1


def _offset_example(section_index: int | None, offset: object, text: object) -> dict[str, object]:
    example: dict[str, object] = {}
    if isinstance(section_index, int) and section_index >= 0:
        example["section"] = section_index
    if isinstance(offset, int):
        example["offset"] = offset
    if text is not None:
        example["text"] = str(text)
    return example


def _compact_value(value: object, depth: int = 0) -> object | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value[:200]
    if isinstance(value, (int, float, bool)):
        return value
    if depth >= 2:
        return None
    if isinstance(value, dict):
        result: dict[str, object] = {}
        for key in sorted(value):
            if not isinstance(key, str):
                continue
            compacted = _compact_value(value[key], depth + 1)
            if compacted is not None:
                result[key] = compacted
        return result if result else None
    if isinstance(value, list):
        result = []
        for item in value[:5]:
            compacted = _compact_value(item, depth + 1)
            if compacted is not None:
                result.append(compacted)
        return result if result else None
    return None


def _compact_example(example: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in sorted(example):
        compacted = _compact_value(example[key])
        if compacted is not None:
            result[key] = compacted
    return result


def write_usage_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_xrefs(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_snippet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_variant_index(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_type_flow_report(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def type_flow_snapshot_path(output_dir: Path, name: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    if not safe:
        safe = "snapshot"
    return output_dir / f"{safe}.jsonl"


def write_type_flow_snapshot(
    report_path: Path = DEFAULT_TYPE_FLOW_REPORT_OUTPUT,
    output_dir: Path = DEFAULT_TYPE_FLOW_SNAPSHOT_DIR,
    *,
    name: str,
) -> Path:
    rows = read_type_flow_report(report_path)
    snapshot_path = type_flow_snapshot_path(output_dir, name)
    write_type_flow_report(snapshot_path, rows)
    return snapshot_path


def write_type_flow_delta(path: Path, delta: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(delta, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_usage_manifest(path: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_usage_xrefs(path: Path = DEFAULT_XREF_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_usage_snippet_rows(path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_variant_index(path: Path = DEFAULT_VARIANT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_type_flow_report(path: Path = DEFAULT_TYPE_FLOW_REPORT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_type_flow_delta(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _type_flow_numeric_address_base_reg(text: str) -> int | None:
    match = re.search(r"\$[0-9A-Fa-f]{2,8}(?:\.[wlWL])?\([aA]([0-7])\)", text)
    if match is None:
        return None
    return int(match.group(1))


def _type_flow_assignment_source_for_reg(text: str, base_reg: int) -> str | None:
    pattern = rf"^\s*(?:movea?|lea)\.[bwlBWL]\s+(.+?),\s*[aA]{base_reg}\b"
    match = re.search(pattern, text)
    if match is None:
        return None
    return match.group(1).strip()


def _type_flow_assignment_source_for_named_reg(text: str, reg_name: str) -> str | None:
    pattern = rf"^\s*(?:movea?|lea)\.[bwlBWL]\s+(.+?),\s*{re.escape(reg_name)}\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        return None
    return match.group(1).strip()


def _type_flow_store_to_memory(text: str) -> tuple[str, str] | None:
    match = re.search(r"^\s*move\.([bwlBWL])\s+([dDaA][0-7]),\s*(.+?)(?:\s*;.*)?$", text)
    if match is None:
        return None
    if match.group(1).lower() != "l":
        return None
    dest_expr = match.group(3).strip()
    if _type_flow_operand_is_register(dest_expr):
        return None
    return match.group(2).upper(), dest_expr


def _type_flow_normalized_operand_expr(text: str) -> str:
    lowered = re.sub(r"\s+", "", text.lower())
    return re.sub(r"\.(?:[bwl])(?=$|\))", "", lowered)


def _type_flow_operand_is_register(text: str) -> bool:
    return re.fullmatch(r"[dDaA][0-7]", text.strip()) is not None


def _type_flow_row_is_call_like(row: dict[str, Any]) -> bool:
    text = _string_value(row.get("text")) if isinstance(row, dict) else None
    return text is not None and re.search(r"^\s*(?:jsr|bsr|jmp|trap)\b", text, re.IGNORECASE) is not None


def _type_flow_storage_kind(assignment_source: str, assignment_row: dict[str, Any] | None) -> str:
    source_lower = assignment_source.lower()
    app_refs = assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None
    if "app_" in source_lower or _dict_items(app_refs):
        return "app_slot"
    if "(a7)" in source_lower or "(sp)" in source_lower:
        return "stack_slot"
    return "global_or_base_slot"


def _type_flow_struct_is_specific(struct_name: object) -> bool:
    struct_text = _string_value(struct_name)
    if struct_text is None:
        return False
    normalized = struct_text.strip().lower()
    return normalized not in {"", "void", "void *", "aptr"}


def _type_flow_register_copy_from_call_output(
    target_id: str,
    source_reg: str,
    store_row_index: int,
    rows_by_index: dict[int, dict[str, Any]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, object] | None:
    source_reg = source_reg.upper()
    for row_index in range(store_row_index - 1, max(0, store_row_index - 8) - 1, -1):
        row = rows_by_index.get(row_index)
        if not isinstance(row, dict) or row.get("kind") != "instruction":
            continue
        row_text = _string_value(row.get("text")) or ""
        if re.search(r"^\s*(?:movea?|lea)\.l\b", row_text, re.IGNORECASE) is None:
            continue
        assigned = _type_flow_assignment_source_for_named_reg(row_text, source_reg)
        if assigned is None:
            continue
        assigned_reg = assigned.upper()
        if not re.fullmatch(r"[DA][0-7]", assigned_reg):
            return None
        os_call = _type_flow_nearby_os_call(target_id, row_index - 8, row_index, xrefs_by_row, rows_by_index)
        output_regs = os_call.get("output_regs") if os_call is not None else None
        if isinstance(output_regs, list) and assigned_reg in output_regs:
            output_structs = os_call.get("output_structs_by_reg")
            output_struct = output_structs.get(assigned_reg) if isinstance(output_structs, dict) else None
            return {
                "copy_row_index": row_index,
                "copy_stable_key": row.get("stable_key"),
                "copy_text": (_string_value(row.get("text")) or "").strip(),
                "api_output_reg": assigned_reg,
                "api_output_struct": output_struct,
                "os_call": os_call,
            }
        return None
    return None


def _type_flow_storage_reload_chain(
    target_id: str,
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    assignment_row_index: int,
    rows: list[dict[str, Any]],
    rows_by_index: dict[int, dict[str, Any]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, object] | None:
    if _type_flow_operand_is_register(assignment_source):
        return None
    storage_key = _type_flow_normalized_operand_expr(assignment_source)
    storage_kind = _type_flow_storage_kind(assignment_source, assignment_row)
    for candidate in reversed(rows):
        candidate_index = candidate.get("row_index")
        if (
            not isinstance(candidate_index, int)
            or candidate_index >= assignment_row_index
            or candidate_index < assignment_row_index - 48
        ):
            continue
        candidate_row = candidate.get("row")
        if not isinstance(candidate_row, dict) or candidate_row.get("kind") != "instruction":
            continue
        store = _type_flow_store_to_memory(_string_value(candidate_row.get("text")) or "")
        if store is None:
            continue
        source_reg, dest_expr = store
        if _type_flow_normalized_operand_expr(dest_expr) != storage_key:
            continue
        os_call = _type_flow_nearby_os_call(target_id, candidate_index - 8, candidate_index, xrefs_by_row, rows_by_index)
        output_regs = os_call.get("output_regs") if os_call is not None else None
        if isinstance(output_regs, list) and source_reg in output_regs:
            output_structs = os_call.get("output_structs_by_reg")
            output_struct = output_structs.get(source_reg) if isinstance(output_structs, dict) else None
            chain_prefix = "api_output" if _type_flow_struct_is_specific(output_struct) else "api_unstructured_output"
            chain = f"{chain_prefix}_to_{storage_kind}_reload"
            return {
                "kind": chain,
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                "api_output_reg": source_reg,
                "api_output_struct": output_struct,
                "os_call": os_call,
            }
        copied = _type_flow_register_copy_from_call_output(
            target_id, source_reg, candidate_index, rows_by_index, xrefs_by_row
        )
        if copied is not None:
            chain_prefix = (
                "api_output_copy"
                if _type_flow_struct_is_specific(copied.get("api_output_struct"))
                else "api_unstructured_output_copy"
            )
            chain = f"{chain_prefix}_to_{storage_kind}_reload"
            return {
                "kind": chain,
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                **copied,
            }
        if os_call is not None:
            chain = f"api_call_to_{storage_kind}_reload_unknown_output"
            return {
                "kind": chain,
                "storage_kind": storage_kind,
                "storage": assignment_source,
                "store_row_index": candidate_index,
                "store_stable_key": candidate_row.get("stable_key"),
                "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
                "store_source_reg": source_reg,
                "os_call": os_call,
            }
        return {
            "kind": f"register_to_{storage_kind}_reload",
            "storage_kind": storage_kind,
            "storage": assignment_source,
            "store_row_index": candidate_index,
            "store_stable_key": candidate_row.get("stable_key"),
            "store_text": (_string_value(candidate_row.get("text")) or "").strip(),
            "store_source_reg": source_reg,
        }
    return None


def _type_flow_rows_for_target(snippet_rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows_by_target: dict[str, list[dict[str, Any]]] = {}
    for snippet in snippet_rows:
        target_id = _string_value(snippet.get("target_id"))
        if target_id is None:
            continue
        rows_by_target.setdefault(target_id, []).append(snippet)
    for rows in rows_by_target.values():
        rows.sort(key=lambda item: int(item.get("row_index", -1)) if isinstance(item.get("row_index"), int) else -1)
    return rows_by_target


def _type_flow_xrefs_by_target_row(xrefs: list[dict[str, Any]]) -> dict[tuple[str, int], list[dict[str, Any]]]:
    by_row: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        row_index = xref.get("row_index")
        if target_id is None or not isinstance(row_index, int):
            continue
        by_row.setdefault((target_id, row_index), []).append(xref)
    return by_row


def _type_flow_rows_by_index(rows_by_target: dict[str, list[dict[str, Any]]], target_id: str) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for snippet in rows_by_target.get(target_id, []):
        row_index = snippet.get("row_index")
        row = snippet.get("row")
        if isinstance(row_index, int) and isinstance(row, dict):
            result[row_index] = row
    return result


def _type_flow_nearby_os_call(
    target_id: str,
    start_row: int,
    end_row: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> dict[str, object] | None:
    for row_index in range(end_row, max(0, start_row) - 1, -1):
        row_xrefs = xrefs_by_row.get((target_id, row_index), [])
        for xref in row_xrefs:
            if _string_value(xref.get("kind")) == "os_call":
                row = rows_by_index.get(row_index, {})
                output_regs = sorted(
                    {
                        str(output.get("value")).upper()
                        for output in row_xrefs
                        if _string_value(output.get("kind")) == "os_call_output"
                        and _string_value(output.get("value"))
                    }
                )
                output_structs_by_reg = {
                    str(output.get("access")).upper(): str(output.get("value"))
                    for output in row_xrefs
                    if _string_value(output.get("kind")) == "os_call_output_struct"
                    and _string_value(output.get("access"))
                    and _string_value(output.get("value"))
                }
                return {
                    "row_index": row_index,
                    "feature": xref.get("feature"),
                    "stable_key": xref.get("stable_key") or row.get("stable_key"),
                    "resolution": xref.get("resolution"),
                    "text": _string_value(xref.get("text")) or (_string_value(row.get("text")) or "").strip(),
                    "output_regs": output_regs,
                    "output_structs_by_reg": output_structs_by_reg,
                    "structured_output_regs": sorted(
                        reg for reg, struct in output_structs_by_reg.items() if _type_flow_struct_is_specific(struct)
                    ),
                }
        row = rows_by_index.get(row_index)
        if isinstance(row, dict) and _type_flow_row_is_call_like(row):
            return None
    return None


def _type_flow_nearby_has_os_call(
    target_id: str,
    start_row: int,
    end_row: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]] | None = None,
) -> bool:
    return _type_flow_nearby_os_call(target_id, start_row, end_row, xrefs_by_row, rows_by_index or {}) is not None


def _type_flow_numeric_access_cause(
    target_id: str,
    snippet: dict[str, Any],
    rows_by_target: dict[str, list[dict[str, Any]]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> str:
    return str(
        _type_flow_numeric_access_trace(target_id, snippet, rows_by_target, xrefs_by_row).get(
            "cause", "unknown_pointer_chain"
        )
    )


def _type_flow_numeric_source_kind(
    assignment_source: str,
    assignment_row: dict[str, Any] | None,
    target_id: str,
    assignment_row_index: int,
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
    rows_by_index: dict[int, dict[str, Any]],
) -> str:
    source_lower = assignment_source.lower()
    app_refs = assignment_row.get("app_slot_refs") if isinstance(assignment_row, dict) else None
    if "app_" in source_lower or _dict_items(app_refs):
        return "app_slot_load"
    if "(a7)" in source_lower or "(sp)" in source_lower:
        return "stack_slot_load"
    if re.fullmatch(r"[da][0-7]", source_lower):
        os_call = _type_flow_nearby_os_call(
            target_id, assignment_row_index - 8, assignment_row_index, xrefs_by_row, rows_by_index
        )
        if os_call is not None:
            output_regs = os_call.get("output_regs")
            if isinstance(output_regs, list) and source_lower.upper() in output_regs:
                return "api_output_nearby"
            if isinstance(output_regs, list) and output_regs:
                return "post_call_register_copy"
            return "api_output_nearby_unknown_output"
    if re.search(r"\([aA][0-7]\)", assignment_source):
        return "unknown_pointer_chain"
    if source_lower.startswith("$") or re.search(r"\$[0-9a-f]{4,8}(?:\.[wl])?$", source_lower):
        return "global_or_base_slot_load"
    return "global_or_base_slot_load"


def _type_flow_numeric_access_trace(
    target_id: str,
    snippet: dict[str, Any],
    rows_by_target: dict[str, list[dict[str, Any]]],
    xrefs_by_row: dict[tuple[str, int], list[dict[str, Any]]],
) -> dict[str, object]:
    row = snippet.get("row")
    text = _string_value(row.get("text")) if isinstance(row, dict) else None
    row_index = snippet.get("row_index")
    trace: dict[str, object] = {}
    if text is None or not isinstance(row_index, int):
        trace["cause"] = "unknown_pointer_chain"
        trace["stop_reason"] = "missing_instruction_text"
        return trace
    base_reg = _type_flow_numeric_address_base_reg(text)
    trace["row_index"] = row_index
    trace["text"] = text.strip()
    if base_reg is None:
        trace["cause"] = "unknown_pointer_chain"
        trace["stop_reason"] = "no_numeric_address_base"
        return trace
    trace["base_register"] = f"A{base_reg}"
    if base_reg == 7:
        trace["cause"] = "stack_slot_load"
        trace["stop_reason"] = "stack_pointer_base"
        return trace
    rows = rows_by_target.get(target_id, [])
    rows_by_index = _type_flow_rows_by_index(rows_by_target, target_id)
    assignment_source: str | None = None
    assignment_row_index = row_index
    assignment_row: dict[str, Any] | None = None
    for candidate in reversed(rows):
        candidate_index = candidate.get("row_index")
        if not isinstance(candidate_index, int) or candidate_index >= row_index or candidate_index < row_index - 16:
            continue
        candidate_row = candidate.get("row")
        if not isinstance(candidate_row, dict) or candidate_row.get("kind") != "instruction":
            continue
        candidate_text = _string_value(candidate_row.get("text")) or ""
        source = _type_flow_assignment_source_for_reg(candidate_text, base_reg)
        if source is None:
            continue
        assignment_source = source
        assignment_row_index = candidate_index
        assignment_row = candidate_row
        break
    if assignment_source is None:
        os_call = _type_flow_nearby_os_call(target_id, row_index - 8, row_index, xrefs_by_row, rows_by_index)
        if os_call is not None:
            trace["cause"] = "post_call_existing_base"
            trace["nearest_os_call"] = os_call
            trace["stop_reason"] = "existing_base_access_after_nearby_os_call"
            return trace
        trace["cause"] = "unknown_pointer_chain"
        trace["stop_reason"] = "no_assignment_to_base_register"
        return trace
    cause = _type_flow_numeric_source_kind(
        assignment_source, assignment_row, target_id, assignment_row_index, xrefs_by_row, rows_by_index
    )
    storage_chain = _type_flow_storage_reload_chain(
        target_id, assignment_source, assignment_row, assignment_row_index, rows, rows_by_index, xrefs_by_row
    )
    trace["cause"] = cause
    trace["assignment"] = {
        "row_index": assignment_row_index,
        "stable_key": assignment_row.get("stable_key") if isinstance(assignment_row, dict) else None,
        "source": assignment_source,
        "text": (_string_value(assignment_row.get("text")) or "").strip() if isinstance(assignment_row, dict) else None,
    }
    if storage_chain is not None:
        trace["propagation_chain"] = storage_chain
    os_call = _type_flow_nearby_os_call(target_id, assignment_row_index - 8, assignment_row_index, xrefs_by_row, rows_by_index)
    if os_call is not None:
        trace["nearest_os_call"] = os_call
    if cause == "unknown_pointer_chain":
        trace["stop_reason"] = "assignment_source_is_address_register_memory_chain"
    elif cause == "api_output_nearby":
        trace["stop_reason"] = "assignment_source_is_register_after_nearby_os_call"
    elif cause == "api_output_nearby_unknown_output":
        trace["stop_reason"] = "assignment_source_is_register_after_call_without_output_metadata"
    elif cause == "post_call_register_copy":
        trace["stop_reason"] = "assignment_source_is_not_nearest_call_output_register"
    elif cause == "app_slot_load":
        trace["stop_reason"] = "assignment_source_is_app_slot"
    elif cause == "stack_slot_load":
        trace["stop_reason"] = "assignment_source_is_stack_slot"
    else:
        trace["stop_reason"] = "assignment_source_is_global_or_base_slot"
    return trace


def build_type_flow_report(
    manifest_rows: list[dict[str, Any]],
    xrefs: list[dict[str, Any]],
    snippet_rows: list[dict[str, Any]],
) -> list[dict[str, object]]:
    manifest_by_id = {
        str(row.get("id")): row
        for row in manifest_rows
        if isinstance(row.get("id"), str)
    }
    reports: dict[str, dict[str, Any]] = {}

    def report_for(target_id: str) -> dict[str, Any]:
        report = reports.get(target_id)
        if report is not None:
            return report
        manifest = manifest_by_id.get(target_id, {})
        report = {
            "schema_version": 1,
            "target_id": target_id,
            "source_id": manifest.get("source_id"),
            "platform": manifest.get("platform"),
            "origin": manifest.get("origin") if isinstance(manifest.get("origin"), dict) else {},
            "counts": {},
            "struct_counts": {},
            "field_counts": {},
            "numeric_cause_counts": {},
            "propagation_chain_counts": {},
            "examples": {},
        }
        reports[target_id] = report
        return report

    def bump(report: dict[str, Any], key: str, count: int = 1) -> None:
        counts = report["counts"]
        counts[key] = int(counts.get(key, 0)) + count

    def bump_map(report: dict[str, Any], map_key: str, key: str) -> None:
        values = report[map_key]
        values[key] = int(values.get(key, 0)) + 1

    def add_example(report: dict[str, Any], key: str, example: dict[str, object]) -> None:
        examples = report["examples"].setdefault(key, [])
        if len(examples) < MAX_EXAMPLES:
            examples.append(_compact_example(example))

    for xref in xrefs:
        target_id = _string_value(xref.get("target_id"))
        feature = _string_value(xref.get("feature")) or ""
        kind = _string_value(xref.get("kind")) or ""
        if target_id is None:
            continue
        report = report_for(target_id)
        example = {
            "feature": feature,
            "kind": kind,
            "section": xref.get("section"),
            "offset": xref.get("offset"),
            "row_index": xref.get("row_index"),
            "stable_key": xref.get("stable_key"),
            "symbol": xref.get("symbol"),
            "value": xref.get("value"),
            "text": xref.get("text"),
        }
        if kind == "platform_typed_access" and feature == "platform_typed_access:any":
            bump(report, "resolved_typed_access")
            add_example(report, "resolved_typed_access", example)
        elif kind == "platform_unresolved_typed_access" and feature == "typed_base_unresolved_field":
            bump(report, "typed_base_unresolved_field")
            add_example(report, "typed_base_unresolved_field", example)
        elif kind == "app_slot_api_arg" and feature == "app_slot:untyped_api_arg":
            bump(report, "untyped_app_slot_api_arg")
            add_example(report, "untyped_app_slot_api_arg", example)
        elif kind == "app_slot_gap" and feature == "app_slot:gap":
            bump(report, "app_slot_gap")
            add_example(report, "app_slot_gap", example)
        elif kind == "app_slot_field_gap" and feature == "app_slot:field_gap":
            bump(report, "app_slot_field_gap")
            add_example(report, "app_slot_field_gap", example)
        elif kind == "app_slot_suggestion" and feature == "app_slot:suggested_region":
            bump(report, "app_slot_suggested_region")
            add_example(report, "app_slot_suggested_region", example)
        if feature.startswith("platform_typed_access_struct:"):
            bump_map(report, "struct_counts", feature.removeprefix("platform_typed_access_struct:"))
        elif feature.startswith("platform_unresolved_typed_access_struct:"):
            bump_map(report, "struct_counts", feature.removeprefix("platform_unresolved_typed_access_struct:"))
        elif feature.startswith("platform_struct_field:"):
            bump_map(report, "field_counts", feature.removeprefix("platform_struct_field:"))
        elif feature.startswith("app_slot_api_arg_reason:"):
            bump(report, f"untyped_reason:{feature.removeprefix('app_slot_api_arg_reason:')}")

    rows_by_target = _type_flow_rows_for_target(snippet_rows)
    xrefs_by_row = _type_flow_xrefs_by_target_row(xrefs)
    for snippet in snippet_rows:
        target_id = _string_value(snippet.get("target_id"))
        row = snippet.get("row")
        if target_id is None or not isinstance(row, dict):
            continue
        if row.get("kind") != "instruction":
            continue
        if _dict_items(row.get("typed_accesses")):
            continue
        text = _string_value(row.get("text")) or ""
        if re.search(r"\$[0-9A-Fa-f]{2,8}(?:\.[wlWL])?\([aA][0-7]\)", text) is None:
            continue
        report = report_for(target_id)
        trace = _type_flow_numeric_access_trace(target_id, snippet, rows_by_target, xrefs_by_row)
        cause = str(trace.get("cause", "unknown_pointer_chain"))
        propagation_chain = trace.get("propagation_chain")
        propagation_chain_kind = (
            str(propagation_chain.get("kind"))
            if isinstance(propagation_chain, dict) and isinstance(propagation_chain.get("kind"), str)
            else None
        )
        bump(report, "numeric_address_reg_access_without_type")
        bump(report, f"numeric_cause:{cause}")
        bump_map(report, "numeric_cause_counts", cause)
        if propagation_chain_kind:
            bump(report, f"propagation_chain:{propagation_chain_kind}")
            bump_map(report, "propagation_chain_counts", propagation_chain_kind)
            if propagation_chain_kind.startswith("api_output"):
                bump(report, "propagation_gap:api_output_storage_reload_untyped_access")
                bump(report, f"propagation_gap:{propagation_chain_kind}")
                if _string_value(propagation_chain.get("api_output_struct")) == "LIB" and _type_flow_row_is_call_like(row):
                    bump(report, "propagation_gap:library_base_reload_lvo_gap")
                os_call = propagation_chain.get("os_call")
                if isinstance(os_call, dict) and _string_value(os_call.get("resolution")) == "local_helper":
                    bump(report, "propagation_gap:local_helper_output_storage_gap")
        add_example(
            report,
            "numeric_address_reg_access_without_type",
            {
                "row_index": snippet.get("row_index"),
                "stable_key": row.get("stable_key"),
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "text": text.strip(),
                "cause": cause,
                "trace": trace,
            },
        )
        add_example(
            report,
            f"numeric_address_reg_access_without_type:{cause}",
            {
                "row_index": snippet.get("row_index"),
                "stable_key": row.get("stable_key"),
                "section": row.get("section_index"),
                "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                "text": text.strip(),
                "trace": trace,
            },
        )
        if propagation_chain_kind:
            add_example(
                report,
                f"propagation_chain:{propagation_chain_kind}",
                {
                    "row_index": snippet.get("row_index"),
                    "stable_key": row.get("stable_key"),
                    "section": row.get("section_index"),
                    "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                    "text": text.strip(),
                    "trace": trace,
                },
            )
            if propagation_chain_kind.startswith("api_output"):
                if (
                    isinstance(propagation_chain, dict)
                    and _string_value(propagation_chain.get("api_output_struct")) == "LIB"
                    and _type_flow_row_is_call_like(row)
                ):
                    add_example(
                        report,
                        "propagation_gap:library_base_reload_lvo_gap",
                        {
                            "row_index": snippet.get("row_index"),
                            "stable_key": row.get("stable_key"),
                            "section": row.get("section_index"),
                            "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                            "text": text.strip(),
                            "trace": trace,
                        },
                    )
                os_call = propagation_chain.get("os_call") if isinstance(propagation_chain, dict) else None
                if isinstance(os_call, dict) and _string_value(os_call.get("resolution")) == "local_helper":
                    add_example(
                        report,
                        "propagation_gap:local_helper_output_storage_gap",
                        {
                            "row_index": snippet.get("row_index"),
                            "stable_key": row.get("stable_key"),
                            "section": row.get("section_index"),
                            "offset": row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr"),
                            "text": text.strip(),
                            "trace": trace,
                        },
                    )

    result: list[dict[str, object]] = []
    for report in reports.values():
        counts = report["counts"]
        if not counts:
            continue
        opportunity_count = sum(
            int(counts.get(key, 0))
            for key in (
                "untyped_app_slot_api_arg",
                "app_slot_gap",
                "app_slot_field_gap",
                "app_slot_suggested_region",
                "typed_base_unresolved_field",
                "numeric_address_reg_access_without_type",
            )
        )
        report["opportunity_count"] = opportunity_count
        report["resolved_typed_access_count"] = int(counts.get("resolved_typed_access", 0))
        report["counts"] = dict(sorted(counts.items()))
        report["struct_counts"] = dict(sorted(report["struct_counts"].items()))
        report["field_counts"] = dict(sorted(report["field_counts"].items()))
        report["numeric_cause_counts"] = dict(sorted(report["numeric_cause_counts"].items()))
        report["propagation_chain_counts"] = dict(sorted(report["propagation_chain_counts"].items()))
        report["examples"] = {
            key: report["examples"][key]
            for key in sorted(report["examples"])
        }
        result.append(report)
    return sorted(
        result,
        key=lambda row: (
            -int(row.get("opportunity_count", 0)),
            -int(row.get("resolved_typed_access_count", 0)),
            str(row.get("platform")),
            str(row.get("target_id")),
        ),
    )


def _type_flow_int(row: dict[str, Any], key: str) -> int:
    value = row.get(key)
    return value if isinstance(value, int) else 0


def _type_flow_count_map(row: dict[str, Any] | None, key: str) -> dict[str, int]:
    if row is None:
        return {}
    values = row.get(key)
    if not isinstance(values, dict):
        return {}
    return {
        str(name): int(value)
        for name, value in values.items()
        if isinstance(name, str) and isinstance(value, int)
    }


def _type_flow_total_map(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in rows:
        for name, value in _type_flow_count_map(row, key).items():
            totals[name] = totals.get(name, 0) + value
    return dict(sorted(totals.items()))


def _type_flow_delta_map(before: dict[str, int], after: dict[str, int]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for key in sorted(set(before) | set(after)):
        before_value = before.get(key, 0)
        after_value = after.get(key, 0)
        delta = after_value - before_value
        if before_value != 0 or after_value != 0 or delta != 0:
            result[key] = {"before": before_value, "after": after_value, "delta": delta}
    return result


def build_type_flow_report_delta(
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    *,
    max_targets: int = 25,
) -> dict[str, object]:
    before_by_target = {
        str(row.get("target_id")): row
        for row in before_rows
        if isinstance(row.get("target_id"), str)
    }
    after_by_target = {
        str(row.get("target_id")): row
        for row in after_rows
        if isinstance(row.get("target_id"), str)
    }
    before_opportunities = sum(_type_flow_int(row, "opportunity_count") for row in before_by_target.values())
    after_opportunities = sum(_type_flow_int(row, "opportunity_count") for row in after_by_target.values())
    before_resolved = sum(_type_flow_int(row, "resolved_typed_access_count") for row in before_by_target.values())
    after_resolved = sum(_type_flow_int(row, "resolved_typed_access_count") for row in after_by_target.values())
    target_deltas: list[dict[str, object]] = []

    for target_id in sorted(set(before_by_target) | set(after_by_target)):
        before_row = before_by_target.get(target_id)
        after_row = after_by_target.get(target_id)
        before_opportunity = _type_flow_int(before_row or {}, "opportunity_count")
        after_opportunity = _type_flow_int(after_row or {}, "opportunity_count")
        before_resolved_count = _type_flow_int(before_row or {}, "resolved_typed_access_count")
        after_resolved_count = _type_flow_int(after_row or {}, "resolved_typed_access_count")
        opportunity_delta = after_opportunity - before_opportunity
        resolved_delta = after_resolved_count - before_resolved_count
        numeric_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "numeric_cause_counts"),
            _type_flow_count_map(after_row, "numeric_cause_counts"),
        )
        propagation_delta = _type_flow_delta_map(
            _type_flow_count_map(before_row, "propagation_chain_counts"),
            _type_flow_count_map(after_row, "propagation_chain_counts"),
        )
        if (
            opportunity_delta == 0
            and resolved_delta == 0
            and not any(item["delta"] != 0 for item in numeric_delta.values())
            and not any(item["delta"] != 0 for item in propagation_delta.values())
        ):
            continue
        display_row = after_row or before_row or {}
        target_deltas.append(
            {
                "target_id": target_id,
                "source_id": display_row.get("source_id"),
                "platform": display_row.get("platform"),
                "origin": display_row.get("origin") if isinstance(display_row.get("origin"), dict) else {},
                "before_opportunity_count": before_opportunity,
                "after_opportunity_count": after_opportunity,
                "opportunity_delta": opportunity_delta,
                "before_resolved_typed_access_count": before_resolved_count,
                "after_resolved_typed_access_count": after_resolved_count,
                "resolved_typed_access_delta": resolved_delta,
                "numeric_cause_deltas": numeric_delta,
                "propagation_chain_deltas": propagation_delta,
            }
        )

    target_deltas.sort(
        key=lambda row: (
            -abs(int(row.get("resolved_typed_access_delta", 0))),
            -abs(int(row.get("opportunity_delta", 0))),
            str(row.get("platform")),
            str(row.get("target_id")),
        )
    )
    return {
        "schema_version": 1,
        "before_target_count": len(before_by_target),
        "after_target_count": len(after_by_target),
        "totals": {
            "opportunity_count": {
                "before": before_opportunities,
                "after": after_opportunities,
                "delta": after_opportunities - before_opportunities,
            },
            "resolved_typed_access_count": {
                "before": before_resolved,
                "after": after_resolved,
                "delta": after_resolved - before_resolved,
            },
        },
        "count_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "counts"),
            _type_flow_total_map(after_rows, "counts"),
        ),
        "numeric_cause_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "numeric_cause_counts"),
            _type_flow_total_map(after_rows, "numeric_cause_counts"),
        ),
        "propagation_chain_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "propagation_chain_counts"),
            _type_flow_total_map(after_rows, "propagation_chain_counts"),
        ),
        "struct_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "struct_counts"),
            _type_flow_total_map(after_rows, "struct_counts"),
        ),
        "field_deltas": _type_flow_delta_map(
            _type_flow_total_map(before_rows, "field_counts"),
            _type_flow_total_map(after_rows, "field_counts"),
        ),
        "target_deltas": target_deltas[:max_targets],
    }


def feature_summary(rows: list[dict[str, Any]]) -> list[dict[str, object]]:
    target_counts: dict[str, int] = {}
    occurrence_counts: dict[str, int] = {}
    for row in rows:
        counts = row.get("feature_counts")
        if not isinstance(counts, dict):
            continue
        for key, value in counts.items():
            if not isinstance(key, str) or not isinstance(value, int):
                continue
            target_counts[key] = target_counts.get(key, 0) + 1
            occurrence_counts[key] = occurrence_counts.get(key, 0) + value
    return [
        {"feature": key, "target_count": target_counts[key], "occurrence_count": occurrence_counts[key]}
        for key in sorted(target_counts)
    ]


def query_usage_manifest(
    rows: list[dict[str, Any]],
    feature: str,
    *,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    needle = q.casefold().strip() if q else ""
    for row in rows:
        if platform is not None and row.get("platform") != platform:
            continue
        counts = row.get("feature_counts")
        if not isinstance(counts, dict):
            continue
        if feature and feature not in counts:
            continue
        matching_features = _matching_features(counts, feature=feature, group=group)
        if group and not matching_features:
            continue
        haystack = json.dumps(
            {
                "id": row.get("id"),
                "source_id": row.get("source_id"),
                "platform": row.get("platform"),
                "origin": row.get("origin"),
                "tags": row.get("tags"),
            },
            sort_keys=True,
        ).casefold()
        if needle and needle not in haystack:
            continue
        examples = row.get("feature_examples")
        selected_examples: list[object] = []
        if isinstance(examples, dict):
            if feature:
                selected_examples = examples.get(feature, [])
            elif group:
                for key in matching_features:
                    for example in examples.get(key, []):
                        if len(selected_examples) >= MAX_EXAMPLES:
                            break
                        selected_examples.append(example)
        result.append(
            {
                "id": row.get("id"),
                "source_id": row.get("source_id"),
                "platform": row.get("platform"),
                "count": counts.get(feature) if feature else sum(
                    value
                    for key, value in counts.items()
                    if isinstance(key, str)
                    and isinstance(value, int)
                    and (not group or feature_matches_group(key, group))
                ),
                "feature_counts": counts,
                "tags": row.get("tags"),
                "origin": row.get("origin"),
                "examples": selected_examples,
            }
        )
    return sorted(result, key=lambda item: (str(item.get("platform")), str(item.get("id"))))


def query_usage_xrefs(
    xrefs: list[dict[str, Any]],
    *,
    target_id: str | None = None,
    feature: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, object]]:
    needle = q.casefold().strip() if q else ""
    result: list[dict[str, object]] = []
    for xref in xrefs:
        if target_id is not None and xref.get("target_id") != target_id:
            continue
        if feature is not None and xref.get("feature") != feature:
            continue
        if group is not None and not feature_matches_group(_string_value(xref.get("feature")) or "", group):
            continue
        if platform is not None and xref.get("platform") != platform:
            continue
        if needle and needle not in json.dumps(xref, sort_keys=True).casefold():
            continue
        result.append(cast_xref(xref))
    return sorted(
        result,
        key=lambda row: (
            str(row.get("target_id")),
            str(row.get("feature")),
            _sort_int(row.get("section")),
            _sort_int(row.get("offset")),
            _sort_int(row.get("row_index")),
            str(row.get("id")),
        ),
    )


def feature_matches_group(feature: str, group: str | None) -> bool:
    if not group:
        return True
    prefixes = FEATURE_GROUPS.get(group)
    if prefixes is None:
        return False
    return any(feature.startswith(prefix) for prefix in prefixes)


def _matching_features(counts: dict[object, object], *, feature: str, group: str | None) -> list[str]:
    if feature:
        return [feature] if feature in counts and feature_matches_group(feature, group) else []
    return sorted(
        key
        for key in counts
        if isinstance(key, str) and feature_matches_group(key, group)
    )


def cast_xref(row: dict[str, Any]) -> dict[str, object]:
    return {key: row.get(key) for key in (
        "schema_version",
        "id",
        "target_id",
        "feature",
        "kind",
        "platform",
        "source_id",
        "origin",
        "section",
        "offset",
        "row_index",
        "stable_key",
        "source_stable_key",
        "symbol",
        "access",
        "resolution",
        "value",
        "text",
    )}


def _print_feature_summary(rows: list[dict[str, Any]], *, json_output: bool) -> None:
    summary = feature_summary(rows)
    if json_output:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    for item in summary:
        print(f"{item['target_count']:5d} {item['occurrence_count']:7d} {item['feature']}")


def _print_query(rows: list[dict[str, Any]], feature: str, *, group: str | None, platform: str | None, json_output: bool) -> None:
    matches = query_usage_manifest(rows, feature, group=group, platform=platform)
    if json_output:
        print(json.dumps(matches, indent=2, sort_keys=True))
        return
    for item in matches:
        print(f"{item['platform']} {item['source_id']} count={item['count']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and query corpus-wide target usage features.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build")
    build.add_argument("--disk-manifest", type=Path, default=DEFAULT_DISK_MANIFEST)
    build.add_argument("--file-manifest", type=Path, default=DEFAULT_FILE_MANIFEST)
    build.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    build.add_argument("--xrefs-output", type=Path, default=DEFAULT_XREF_OUTPUT)
    build.add_argument("--snippet-rows-output", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    build.add_argument("--variants-output", type=Path, default=DEFAULT_VARIANT_OUTPUT)
    build.add_argument("--type-flow-report-output", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)

    list_features = subparsers.add_parser("list-features")
    list_features.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    list_features.add_argument("--json", action="store_true")

    query = subparsers.add_parser("query")
    query.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    query.add_argument("--feature", default="")
    query.add_argument("--group")
    query.add_argument("--platform")
    query.add_argument("--json", action="store_true")

    type_flow_report = subparsers.add_parser("type-flow-report")
    type_flow_report.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    type_flow_report.add_argument("--xrefs", type=Path, default=DEFAULT_XREF_OUTPUT)
    type_flow_report.add_argument("--snippet-rows", type=Path, default=DEFAULT_SNIPPET_ROWS_OUTPUT)
    type_flow_report.add_argument("--output", type=Path)
    type_flow_report.add_argument("--json", action="store_true")

    type_flow_delta = subparsers.add_parser("type-flow-delta")
    type_flow_delta.add_argument("--before", type=Path, required=True)
    type_flow_delta.add_argument("--after", type=Path, required=True)
    type_flow_delta.add_argument("--output", type=Path)
    type_flow_delta.add_argument("--max-targets", type=int, default=25)
    type_flow_delta.add_argument("--json", action="store_true")

    type_flow_snapshot = subparsers.add_parser("type-flow-snapshot")
    type_flow_snapshot.add_argument("--report", type=Path, default=DEFAULT_TYPE_FLOW_REPORT_OUTPUT)
    type_flow_snapshot.add_argument("--output-dir", type=Path, default=DEFAULT_TYPE_FLOW_SNAPSHOT_DIR)
    type_flow_snapshot.add_argument("--name", required=True)
    type_flow_snapshot.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "build":
        rows, xrefs, snippet_rows = build_usage_outputs(args.disk_manifest, args.file_manifest)
        variant_rows = build_variant_index(args.file_manifest)
        type_flow_rows = build_type_flow_report(rows, xrefs, snippet_rows)
        write_usage_manifest(args.output, rows)
        write_usage_xrefs(args.xrefs_output, xrefs)
        write_usage_snippet_rows(args.snippet_rows_output, snippet_rows)
        write_variant_index(args.variants_output, variant_rows)
        write_type_flow_report(args.type_flow_report_output, type_flow_rows)
        print(f"Wrote {args.output}")
        print(f"Wrote {args.xrefs_output}")
        print(f"Wrote {args.snippet_rows_output}")
        print(f"Wrote {args.variants_output}")
        print(f"Wrote {args.type_flow_report_output}")
        print(f"Entries: {len(rows)}")
        print(f"Xrefs: {len(xrefs)}")
        print(f"Snippet rows: {len(snippet_rows)}")
        print(f"Variants: {len(variant_rows)}")
        print(f"Type-flow report rows: {len(type_flow_rows)}")
        return 0
    if args.command == "list-features":
        rows = read_usage_manifest(args.manifest)
        _print_feature_summary(rows, json_output=bool(args.json))
        return 0
    if args.command == "query":
        rows = read_usage_manifest(args.manifest)
        _print_query(rows, args.feature, group=args.group, platform=args.platform, json_output=bool(args.json))
        return 0
    if args.command == "type-flow-report":
        rows = read_usage_manifest(args.manifest)
        type_flow_rows = build_type_flow_report(rows, read_usage_xrefs(args.xrefs), read_usage_snippet_rows(args.snippet_rows))
        if args.output is not None:
            write_type_flow_report(args.output, type_flow_rows)
        if args.json or args.output is None:
            print(json.dumps(type_flow_rows, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-delta":
        delta = build_type_flow_report_delta(
            read_type_flow_report(args.before),
            read_type_flow_report(args.after),
            max_targets=max(0, int(args.max_targets)),
        )
        if args.output is not None:
            write_type_flow_delta(args.output, delta)
        if args.json or args.output is None:
            print(json.dumps(delta, indent=2, sort_keys=True))
        return 0
    if args.command == "type-flow-snapshot":
        snapshot_path = write_type_flow_snapshot(args.report, args.output_dir, name=str(args.name))
        if args.json:
            print(json.dumps({"path": str(snapshot_path)}, indent=2, sort_keys=True))
        else:
            print(f"Wrote {snapshot_path}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
