"""Listing source adapter for selected Classic Mac OS CODE resources."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.api import ListingWindowPayload
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_listing_artifact_profile_from_binary_source,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_image import read_macos_hfs_image_bytes
from amiga_reversing.disasm.macos_project_origin import macos_code_source_descriptor_from_project
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectRecord


def build_macos_project_listing_artifact_profile(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[int, dict[str, object], MacosCodeListingArtifact]:
    descriptor = macos_code_source_descriptor_from_project(project, project_root=project_root)
    listing_source = build_macos_code_listing_source(project, project_root=project_root)
    total_rows, profile, artifact = build_listing_artifact_profile_from_binary_source(
        descriptor,
        project_root=project_root,
    )
    macos_artifact = MacosCodeListingArtifact(artifact, listing_source)
    summary, _summary_profile = macos_artifact.summary_payload()
    adjusted_total = summary.get("total_rows")
    return adjusted_total if isinstance(adjusted_total, int) else total_rows, _macos_profile(profile), macos_artifact


def build_macos_code_listing_source(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    descriptor = macos_code_source_descriptor_from_project(project, project_root=project_root)
    image_relpath = _display_source_image(descriptor.source_image, project_root)
    hfs_path = descriptor.hfs_path
    resource_id = descriptor.resource_id
    hfs_bytes = read_macos_hfs_image_bytes(descriptor.source_image)
    summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    code_bytes = extract_macos_hfs_code_resource_bytes_with_c_backend(hfs_bytes, hfs_path, resource_id)
    if not code_bytes:
        raise ValueError(f"Mac OS project {project.id} selected CODE {resource_id} has no code bytes")
    selected_code = _mapping(summary.get("selected_code"))
    selected_range = _selected_executable_range(summary, resource_id)
    resource = _code_resource_by_id(_sequence(_mapping(summary.get("resource_fork")).get("code_resources")), resource_id)
    file_info = _mapping(summary.get("file"))
    return {
        "project_id": project.id,
        "platform": "macos",
        "source_image": image_relpath,
        "hfs_path": hfs_path,
        "fork": "resource",
        "resource_type": "CODE",
        "resource_id": resource_id,
        "resource_name": resource.get("name") or selected_code.get("name"),
        "source_descriptor": _macos_source_descriptor_payload(descriptor, project_root),
        "resource": resource,
        "selected_code": selected_code,
        "classified_range": selected_range,
        "executable_deferred": _sequence(summary.get("executable_deferred")),
        "code_bytes": code_bytes,
        "display_path": f"{hfs_path} CODE {resource_id} {resource.get('name') or selected_code.get('name') or ''}".strip(),
        "container": {
            "kind": summary.get("container_kind"),
            "file_type": file_info.get("type"),
            "creator": file_info.get("creator"),
            "cnid": file_info.get("cnid"),
        },
        "unsupported": _sequence(summary.get("unsupported")),
    }


def macos_listing_cache_key(project: ProjectRecord, *, project_root: Path = PROJECT_ROOT) -> str:
    descriptor = macos_code_source_descriptor_from_project(project, project_root=project_root)
    target_dir = project_root / project.target_dir
    return "|".join(
        [
            project.id,
            descriptor.stable_cache_identity,
            _file_cache_stamp(descriptor.source_image),
            _file_cache_stamp(target_dir / ".project.json"),
        ]
    )


class MacosCodeListingArtifact:
    def __init__(self, wrapped: CListingArtifact, listing_source: Mapping[str, object]) -> None:
        self._wrapped = wrapped
        self._listing_source = listing_source
        self._provenance = _macos_row_provenance(listing_source)

    def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        analysis, profile = self._wrapped.analysis_payload()
        adjusted = dict(analysis)
        selected_range = _mapping(self._provenance.get("classified_range"))
        adjusted["platform"] = "macos"
        adjusted["executable_model"] = "platform_executable_summary_v1"
        adjusted["executable_ranges"] = [dict(selected_range)] if selected_range else []
        adjusted["executable_deferred"] = list(_sequence(self._listing_source.get("executable_deferred")))
        adjusted["macos"] = self._provenance
        return adjusted, _macos_profile(profile)

    def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
        source_text, profile = self._wrapped.source_text_with_profile()
        return _macos_source_text(self._listing_source, source_text), _macos_profile(profile)

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        summary, profile = self._wrapped.summary_payload()
        adjusted = dict(summary)
        adjusted["platform"] = "macos"
        adjusted["backend"] = "macos-code"
        adjusted["macos"] = self._provenance
        total_rows = adjusted.get("total_rows")
        if isinstance(total_rows, int):
            adjusted["total_rows"] = max(0, total_rows - 1)
        return adjusted, _macos_profile(profile)

    def navigation_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        navigation, profile = self._wrapped.navigation_payload()
        adjusted = dict(navigation)
        adjusted["macos"] = self._provenance
        return adjusted, _macos_profile(profile)

    def window_payload(self, *, start: int, count: int) -> tuple[ListingWindowPayload, dict[str, object]]:
        payload, profile = self._wrapped.window_payload(start=start, count=count)
        return self._macos_window(payload), _macos_profile(profile)

    def addr_window_payload(
        self,
        *,
        addr: int | None,
        before: int,
        after: int,
    ) -> tuple[ListingWindowPayload, dict[str, object]]:
        payload, profile = self._wrapped.addr_window_payload(addr=addr, before=before, after=after)
        return self._macos_window(payload), _macos_profile(profile)

    def anchor_window_payload(self, *, anchor_code: str, count: int) -> tuple[ListingWindowPayload, dict[str, object]]:
        payload, profile = self._wrapped.anchor_window_payload(anchor_code=anchor_code, count=count)
        return self._macos_window(payload), _macos_profile(profile)

    def row_for_source_offset(self, *, section_index: int | None, offset: int) -> dict[str, object] | None:
        row = self._wrapped.row_for_source_offset(section_index=section_index, offset=offset)
        return _macos_row(row, self._provenance) if row is not None else None

    def row_for_runtime_address(self, *, address: int) -> dict[str, object] | None:
        row = self._wrapped.row_for_runtime_address(address=address)
        return _macos_row(row, self._provenance) if row is not None else None

    def close(self) -> None:
        self._wrapped.close()

    def _macos_window(self, payload: ListingWindowPayload) -> ListingWindowPayload:
        rows = [
            row
            for row in (_macos_row(raw_row, self._provenance) for raw_row in payload.get("rows", []))
            if row is not None
        ]
        adjusted = dict(payload)
        adjusted["analysis_generation"] = "macos-code"
        adjusted["rows"] = rows
        total_rows = adjusted.get("total_rows")
        if isinstance(total_rows, int):
            adjusted["total_rows"] = max(0, total_rows - 1)
        start = adjusted.get("start", 0)
        adjusted["end"] = (start if isinstance(start, int) else 0) + len(rows)
        return cast(ListingWindowPayload, adjusted)


def _display_source_image(source_image: Path, project_root: Path) -> str:
    try:
        return source_image.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return source_image.as_posix()


def _macos_source_descriptor_payload(descriptor: object, project_root: Path) -> dict[str, object]:
    source_image = cast(Path, getattr(descriptor, "source_image"))
    return {
        "kind": str(getattr(descriptor, "kind")),
        "source_image": _display_source_image(source_image, project_root),
        "hfs_path": getattr(descriptor, "hfs_path"),
        "resource_type": getattr(descriptor, "resource_type"),
        "resource_id": getattr(descriptor, "resource_id"),
        "resource_name": getattr(descriptor, "resource_name"),
        "address_model": str(getattr(descriptor, "address_model")),
        "cache_identity": getattr(descriptor, "stable_cache_identity"),
        "display_path": getattr(descriptor, "display_path"),
    }


def _code_resource_by_id(resources: list[object], resource_id: int) -> Mapping[str, object]:
    for resource in resources:
        mapping = _mapping(resource)
        if mapping.get("id") == resource_id:
            return mapping
    return {}


def _selected_executable_range(summary: Mapping[str, object], resource_id: int) -> Mapping[str, object]:
    if summary.get("executable_model") != "platform_executable_summary_v1":
        raise ValueError("Mac OS CODE listing requires shared executable ranges")
    for item in _sequence(summary.get("executable_ranges")):
        range_info = _mapping(item)
        if (
            range_info.get("resource_type") == "CODE"
            and range_info.get("resource_id") == resource_id
            and range_info.get("role") in {"code", "candidate_code"}
            and range_info.get("entrypoint") is True
        ):
            return range_info
    raise ValueError(f"Mac OS CODE {resource_id} listing requires a shared executable code range")


def _macos_row_provenance(listing_source: Mapping[str, object]) -> dict[str, object]:
    selected_range = _mapping(listing_source.get("classified_range"))
    return {
        "platform": "macos",
        "hfs_path": listing_source.get("hfs_path"),
        "fork": listing_source.get("fork"),
        "resource_type": listing_source.get("resource_type"),
        "resource_id": listing_source.get("resource_id"),
        "resource_name": listing_source.get("resource_name"),
        "classified_range": selected_range,
        "code_resource_offset_base": selected_range.get("load_offset"),
    }


def _macos_profile(profile: Mapping[str, object]) -> dict[str, object]:
    adjusted = dict(profile)
    adjusted["backend"] = "macos-code"
    adjusted["source_kind"] = "macos_code_resource"
    adjusted.pop("wrapped_backend", None)
    return adjusted


def _macos_source_text(listing_source: Mapping[str, object], source_text: str) -> str:
    provenance = _macos_row_provenance(listing_source)
    selected_range = _mapping(provenance.get("classified_range"))
    header = [
        "; Classic Mac OS CODE resource listing",
        "; source kind: macos_code_resource",
        f"; HFS path: {provenance.get('hfs_path')}",
        f"; fork: {provenance.get('fork')}",
        (
            f"; resource: {provenance.get('resource_type')} {provenance.get('resource_id')} "
            f"{provenance.get('resource_name') or ''}"
        ).rstrip(),
        (
            f"; classified_range: {selected_range.get('role')} "
            f"payload[{selected_range.get('load_offset')}.."
            f"{_range_end(selected_range)}) "
            f"evidence={selected_range.get('evidence')}"
        ),
        "",
    ]
    body = [line for line in source_text.rstrip().splitlines() if not _is_amiga_section_line(line)]
    return "\n".join([*header, *body, ""])


def _macos_row(row: dict[str, object] | None, provenance: Mapping[str, object]) -> dict[str, object] | None:
    if row is None:
        return None
    text = str(row.get("text") or "")
    if _is_amiga_section_line(text):
        return None
    adjusted = dict(row)
    adjusted["macos"] = dict(provenance)
    return adjusted


def _is_amiga_section_line(text: str) -> bool:
    return text.strip().lower() == "section code,code"


def _range_end(range_info: Mapping[str, object]) -> object:
    start = range_info.get("load_offset")
    size = range_info.get("size")
    if isinstance(start, int) and isinstance(size, int):
        return start + size
    return None


def _file_cache_stamp(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return f"{path}:missing"
    return f"{path}:{stat.st_size}:{stat.st_mtime_ns}"


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []
