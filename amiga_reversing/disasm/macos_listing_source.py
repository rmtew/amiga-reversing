"""Listing source adapter for selected Classic Mac OS CODE resources."""

from __future__ import annotations

import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

from amiga_reversing.disasm.api import ListingWindowPayload
from amiga_reversing.disasm.binary_source import (
    BinarySourceKind,
    RawAddressModel,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    CListingArtifact,
    build_listing_artifact_profile_from_binary_source,
    extract_macos_hfs_code_resource_bytes_with_c_backend,
    inspect_macos_hfs_code_summary_with_c_backend,
)
from amiga_reversing.disasm.macos_asm_container import (
    MPW_ASM_PATH,
    read_macos_hfs_image_bytes,
)
from amiga_reversing.disasm.macos_project_origin import is_macos_project_origin
from amiga_reversing.disasm.project_paths import PROJECT_ROOT
from amiga_reversing.disasm.projects import ProjectRecord


def build_macos_project_listing_artifact_profile(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[int, dict[str, object], MacosCodeListingArtifact]:
    listing_source = build_macos_code_listing_source(project, project_root=project_root)
    with _temporary_code_binary_source(listing_source, project_root=project_root) as binary_source:
        total_rows, profile, artifact = build_listing_artifact_profile_from_binary_source(
            binary_source,
            project_root=project_root,
        )
    macos_artifact = MacosCodeListingArtifact(artifact, listing_source)
    summary, _summary_profile = macos_artifact.summary_payload()
    adjusted_total = summary.get("total_rows")
    return adjusted_total if isinstance(adjusted_total, int) else total_rows, profile, macos_artifact


def build_macos_code_listing_source(
    project: ProjectRecord,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    origin = _macos_origin(project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    resource_id = _selected_resource_id(origin)
    hfs_bytes = read_macos_hfs_image_bytes(project_root / image_relpath)
    summary = inspect_macos_hfs_code_summary_with_c_backend(hfs_bytes, hfs_path)
    code_bytes = extract_macos_hfs_code_resource_bytes_with_c_backend(hfs_bytes, hfs_path, resource_id)
    if not code_bytes:
        raise ValueError(f"Mac OS project {project.id} selected CODE {resource_id} has no code bytes")
    selected_code = _mapping(summary.get("selected_code"))
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
        "resource": resource,
        "selected_code": selected_code,
        "classified_range": _selected_executable_range(selected_code),
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
    origin = _macos_origin(project)
    image_relpath = _required_string(origin, "source_image")
    hfs_path = str(origin.get("hfs_path") or MPW_ASM_PATH)
    resource_id = _selected_resource_id(origin)
    target_dir = project_root / project.target_dir
    return "|".join(
        [
            project.id,
            "macos-code-resource",
            image_relpath,
            _file_cache_stamp(project_root / image_relpath),
            hfs_path,
            f"CODE:{resource_id}",
            _file_cache_stamp(target_dir / ".project.json"),
        ]
    )


class MacosCodeListingArtifact:
    def __init__(self, wrapped: CListingArtifact, listing_source: Mapping[str, object]) -> None:
        self._wrapped = wrapped
        self._listing_source = listing_source
        self._provenance = _macos_row_provenance(listing_source)

    def analysis_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        return self._wrapped.analysis_payload()

    def source_text_with_profile(self) -> tuple[str, dict[str, object]]:
        source_text, profile = self._wrapped.source_text_with_profile()
        return _macos_source_text(self._listing_source, source_text), _macos_profile(profile)

    def summary_payload(self) -> tuple[dict[str, object], dict[str, object]]:
        summary, profile = self._wrapped.summary_payload()
        adjusted = dict(summary)
        adjusted["platform"] = "macos"
        adjusted["backend"] = "macos-code"
        adjusted["macos"] = self._provenance
        if isinstance(adjusted.get("total_rows"), int):
            adjusted["total_rows"] = max(0, int(adjusted["total_rows"]) - 1)
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
        if isinstance(adjusted.get("total_rows"), int):
            adjusted["total_rows"] = max(0, int(adjusted["total_rows"]) - 1)
        adjusted["end"] = int(adjusted.get("start", 0)) + len(rows)
        return adjusted  # type: ignore[return-value]


@contextmanager
def _temporary_code_binary_source(
    listing_source: Mapping[str, object],
    *,
    project_root: Path,
) -> Iterator[RawBinarySource]:
    code_bytes = listing_source.get("code_bytes")
    if not isinstance(code_bytes, bytes):
        raise TypeError("Mac CODE listing source requires code_bytes")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".macos-code.bin") as temp_file:
            temp_file.write(code_bytes)
            temp_path = Path(temp_file.name)
        yield RawBinarySource(
            kind=BinarySourceKind.RAW_BINARY,
            path=temp_path,
            address_model=RawAddressModel.LOCAL_OFFSET,
            load_address=0,
            entrypoint=0,
            code_start_offset=0,
            display_path=str(listing_source.get("display_path") or "Mac OS CODE resource"),
            analysis_cache_path=project_root / "targets" / ".macos-code.analysis",
        )
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _macos_origin(project: ProjectRecord) -> Mapping[str, object]:
    origin = project.origin
    if not is_macos_project_origin(origin):
        raise ValueError("Mac OS listing requires macos_mpw_fixture origin")
    return origin


def _selected_resource_id(origin: Mapping[str, object]) -> int:
    value = origin.get("selected_code_resource_id", 1)
    return value if isinstance(value, int) and value > 0 else 1


def _required_string(origin: Mapping[str, object], key: str) -> str:
    value = origin.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Mac OS project origin missing {key}")
    return value


def _code_resource_by_id(resources: list[object], resource_id: int) -> Mapping[str, object]:
    for resource in resources:
        mapping = _mapping(resource)
        if mapping.get("id") == resource_id:
            return mapping
    return {}


def _selected_executable_range(selected_code: Mapping[str, object]) -> Mapping[str, object]:
    code = _mapping(selected_code.get("code"))
    for item in _sequence(code.get("layout_ranges")):
        range_info = _mapping(item)
        if range_info.get("kind") in {"confirmed_code", "candidate_code"} and range_info.get("entrypoint") is True:
            return range_info
    return {}


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
        "code_resource_offset_base": selected_range.get("start"),
    }


def _macos_profile(profile: Mapping[str, object]) -> dict[str, object]:
    adjusted = dict(profile)
    adjusted["backend"] = "macos-code"
    adjusted["wrapped_backend"] = profile.get("backend")
    return adjusted


def _macos_source_text(listing_source: Mapping[str, object], source_text: str) -> str:
    provenance = _macos_row_provenance(listing_source)
    selected_range = _mapping(provenance.get("classified_range"))
    header = [
        "; Classic Mac OS CODE resource listing",
        f"; HFS path: {provenance.get('hfs_path')}",
        f"; fork: {provenance.get('fork')}",
        (
            f"; resource: {provenance.get('resource_type')} {provenance.get('resource_id')} "
            f"{provenance.get('resource_name') or ''}"
        ).rstrip(),
        (
            f"; classified_range: {selected_range.get('kind')} "
            f"payload[{selected_range.get('start')}..{selected_range.get('end')}) "
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
