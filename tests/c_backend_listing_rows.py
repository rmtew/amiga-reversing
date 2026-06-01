from __future__ import annotations

from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import cast

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySource
from amiga_reversing.disasm.c_backend import ApiCallRowKey
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths

ProjectRowsResult = tuple[list[dict[str, object]], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]


def build_project_listing_rows_with_c_artifact(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> ProjectRowsResult:
    return cast(ProjectRowsResult, deepcopy(_cached_project_listing_rows(project_name, str(project_root.resolve()))))


@cache
def _cached_project_listing_rows(project_name: str, project_root_text: str) -> ProjectRowsResult:
    project_root = Path(project_root_text)
    total_rows, profile, artifact = c_backend.build_project_listing_artifact_profile(
        project_name,
        project_root=project_root,
    )
    try:
        payload, window_profile = artifact.window_payload(start=0, count=total_rows)
        navigation, navigation_profile = artifact.navigation_payload()
        app_slot_analysis = navigation.get("app_slot_analysis")
        type_flow_analysis = navigation.get("type_flow_analysis")
        merged_profile = {**profile, **navigation_profile, **window_profile}
        merged_profile["navigation"] = navigation
        if isinstance(app_slot_analysis, dict):
            merged_profile["app_slot_analysis"] = app_slot_analysis
        if isinstance(type_flow_analysis, dict):
            merged_profile["type_flow_analysis"] = type_flow_analysis
        rows = list(payload["rows"])
        return rows, _api_calls_from_rows(rows), merged_profile
    finally:
        artifact.close()


def _listing_artifact_payload(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    project_root: Path,
) -> dict[str, object]:
    with c_backend._source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        artifact = c_backend.CListingArtifact.create(
            source_file,
            metadata_text=metadata_text,
            include_dir=str(c_backend._platform_include_dir_for_listing(source_file.platform_name, project_root)),
            project_root=project_root,
        )
    try:
        summary, summary_profile = artifact.summary_payload()
        analysis, analysis_profile = artifact.analysis_payload()
        total_rows = summary.get("total_rows", 0)
        listing, listing_profile = artifact.window_payload(
            start=0,
            count=total_rows if isinstance(total_rows, int) else 0,
        )
        navigation, navigation_profile = artifact.navigation_payload()
        app_slot_analysis = navigation.get("app_slot_analysis")
        type_flow_analysis = navigation.get("type_flow_analysis")
        merged_profile = {**summary_profile, **analysis_profile, **listing_profile, **navigation_profile}
        merged_profile["navigation"] = navigation
        if isinstance(app_slot_analysis, dict):
            merged_profile["app_slot_analysis"] = app_slot_analysis
        if isinstance(type_flow_analysis, dict):
            merged_profile["type_flow_analysis"] = type_flow_analysis
        return {
            "analysis": analysis,
            "listing": {
                "rows": list(listing["rows"]),
                "app_slot_analysis": app_slot_analysis,
                "type_flow_analysis": type_flow_analysis,
            },
            "navigation": navigation,
            "profile": cast(dict[str, object], merged_profile),
        }
    finally:
        artifact.close()


def build_project_listing_rows_profile_with_c_artifact(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> ProjectRowsResult:
    return build_project_listing_rows_with_c_artifact(project_name, project_root=project_root)


def build_project_listing_rows_from_source_with_c_artifact(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    project_root: Path,
) -> tuple[list[dict[str, object]], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    payload = _listing_artifact_payload(binary_source, metadata_text=metadata_text, project_root=project_root)
    listing = cast(dict[str, object], payload.get("listing", {}))
    rows = cast(list[dict[str, object]], listing.get("rows", []))
    profile = cast(dict[str, object], payload.get("profile", {}))
    return rows, _api_calls_from_rows(rows), profile


def _api_calls_from_rows(rows: list[dict[str, object]]) -> dict[ApiCallRowKey, dict[str, object]]:
    api_calls: dict[ApiCallRowKey, dict[str, object]] = {}
    for row in rows:
        api_call = row.get("api_call")
        if not isinstance(api_call, dict):
            continue
        source_context = row.get("source_context")
        if not isinstance(source_context, dict):
            continue
        hunk_index = source_context.get("hunk_index")
        addr = row.get("addr")
        if isinstance(hunk_index, int) and isinstance(addr, int):
            api_calls[(hunk_index, addr)] = cast(dict[str, object], api_call)
    return api_calls


def analyze_project_with_c_artifact(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    return cast(dict[str, object], deepcopy(_cached_project_analysis(project_name, str(project_root.resolve()))))


@cache
def _cached_project_analysis(project_name: str, project_root_text: str) -> dict[str, object]:
    project_root = Path(project_root_text)
    paths = resolve_project_paths(project_name, project_root=project_root)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        metadata_text = c_backend._metadata_path_text(metadata_path)
        return analyze_source_with_c_artifact(
            paths.binary_source,
            metadata_text=metadata_text,
            project_root=project_root,
        )


def analyze_source_with_c_artifact(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    project_root: Path,
) -> dict[str, object]:
    return _listing_artifact_payload(binary_source, metadata_text=metadata_text, project_root=project_root)
