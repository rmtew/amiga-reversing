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
MAX_EXAMPLES = 5
CPU_NAMES = {
    0: "68000",
    1: "68010",
    2: "68020",
    3: "68030",
    4: "68040",
    5: "68060",
}
FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "os": ("os_call", "os:"),
    "hardware": ("hardware:", "hardware_register:", "value_domain:amiga.custom", "value_domain:amiga.cia"),
    "devices": ("device:", "device_call"),
    "copper": ("data:copper_list", "hardware:custom/copper", "value_domain:amiga.custom.copper"),
    "runtime": ("runtime:",),
    "app_slots": ("app_slot:",),
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
            _add_executable_analysis_features(combined, bag)
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


def _add_executable_analysis_features(combined: dict[str, Any], bag: FeatureBag) -> None:
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
        for effect in _dict_items(section.get("recovered_platform_effects")):
            base_name = _string_value(effect.get("base_name"))
            if base_name:
                bag.add(f"platform_base:{_safe_part(base_name)}", example=_offset_example(section_index, effect.get("offset"), base_name))
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
    for row in _dict_items(listing.get("rows")):
        text = _string_value(row.get("text")) or ""
        opcode_or_directive = (_string_value(row.get("opcode_or_directive")) or "").upper()
        is_equate = bool(re.search(r"(^|\s)EQU(\s|$)", text))
        section_index = _int_value(row.get("section_index"), -1)
        offset = row.get("start_offset") if isinstance(row.get("start_offset"), int) else row.get("addr")
        example = _offset_example(section_index, offset, text.strip()[:160])
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
        for app_ref in _dict_items(row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            bag.add("app_slot:any", example=example)
            bag.add(f"app_slot:{_safe_part(access)}", example=example)


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
        "operand_text",
        "comment_text",
        "data_class",
        "structured_data",
        "app_slot_refs",
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
        for effect in _dict_items(section.get("recovered_platform_effects")):
            offset = _int_value(effect.get("offset"))
            row_index, stable_key, row_text = _row_location(row_locations, section_index, offset)
            base_name = _string_value(effect.get("base_name"))
            if base_name:
                xrefs.append(_xref(row, f"platform_base:{_safe_part(base_name)}", "platform_effect", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=base_name, text=row_text or base_name))
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
                for feature in amiga_hardware_usage.group_features(base, symbol, copper_row=bool(data_class == "copper_list")):
                    if feature not in seen_group_features:
                        seen_group_features.add(feature)
                        xrefs.append(_xref(row, feature, "hardware_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, text=text.strip()))
        for app_ref in _dict_items(listing_row.get("app_slot_refs")):
            access = _string_value(app_ref.get("access")) or "unknown"
            symbol = _string_value(app_ref.get("symbol")) or _app_slot_symbol(app_ref.get("displacement"))
            displacement = _int_value(app_ref.get("displacement"))
            xrefs.append(_xref(row, "app_slot:any", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=text.strip()))
            xrefs.append(_xref(row, f"app_slot:{_safe_part(access)}", "app_slot_ref", section=section_index, offset=offset, row_index=row_index, stable_key=stable_key, symbol=symbol, access=access, value=displacement, text=text.strip()))
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


def _compact_example(example: dict[str, object]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in sorted(example):
        value = example[key]
        if value is None:
            continue
        if isinstance(value, str):
            result[key] = value[:200]
        elif isinstance(value, (int, float, bool)):
            result[key] = value
    return result


def write_usage_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_xrefs(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def write_usage_snippet_rows(path: Path, rows: list[dict[str, object]]) -> None:
    write_jsonl_manifest(path, rows)


def read_usage_manifest(path: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_usage_xrefs(path: Path = DEFAULT_XREF_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


def read_usage_snippet_rows(path: Path = DEFAULT_SNIPPET_ROWS_OUTPUT) -> list[dict[str, Any]]:
    return read_jsonl_manifest(path)


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

    list_features = subparsers.add_parser("list-features")
    list_features.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    list_features.add_argument("--json", action="store_true")

    query = subparsers.add_parser("query")
    query.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    query.add_argument("--feature", default="")
    query.add_argument("--group")
    query.add_argument("--platform")
    query.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "build":
        rows, xrefs, snippet_rows = build_usage_outputs(args.disk_manifest, args.file_manifest)
        write_usage_manifest(args.output, rows)
        write_usage_xrefs(args.xrefs_output, xrefs)
        write_usage_snippet_rows(args.snippet_rows_output, snippet_rows)
        print(f"Wrote {args.output}")
        print(f"Wrote {args.xrefs_output}")
        print(f"Wrote {args.snippet_rows_output}")
        print(f"Entries: {len(rows)}")
        print(f"Xrefs: {len(xrefs)}")
        print(f"Snippet rows: {len(snippet_rows)}")
        return 0
    rows = read_usage_manifest(args.manifest)
    if args.command == "list-features":
        _print_feature_summary(rows, json_output=bool(args.json))
        return 0
    if args.command == "query":
        _print_query(rows, args.feature, group=args.group, platform=args.platform, json_output=bool(args.json))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
