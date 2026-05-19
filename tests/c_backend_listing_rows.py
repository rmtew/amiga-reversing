from __future__ import annotations

from pathlib import Path
from typing import cast

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySource
from amiga_reversing.disasm.c_backend import ApiCallRowKey
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths


def build_project_listing_rows_with_c_artifact(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[dict[str, object]], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    total_rows, profile, artifact = c_backend.build_project_listing_artifact_profile(
        project_name,
        project_root=project_root,
    )
    try:
        payload, window_profile = artifact.window_payload(start=0, count=total_rows)
        navigation, navigation_profile = artifact.navigation_payload()
        merged_profile = {**profile, **navigation_profile, **window_profile}
        app_slot_analysis = navigation.get("app_slot_analysis")
        if isinstance(app_slot_analysis, dict):
            merged_profile["app_slot_analysis"] = app_slot_analysis
        type_flow_analysis = navigation.get("type_flow_analysis")
        if isinstance(type_flow_analysis, dict):
            merged_profile["type_flow_analysis"] = type_flow_analysis
        rows = list(payload["rows"])
        return rows, _api_calls_from_rows(rows), merged_profile
    finally:
        artifact.close()


def build_project_listing_rows_profile_with_c_artifact(
    project_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[dict[str, object]], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    return build_project_listing_rows_with_c_artifact(project_name, project_root=project_root)


def build_project_listing_rows_from_source_with_c_artifact(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    project_root: Path,
) -> tuple[list[dict[str, object]], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    with c_backend._source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        artifact = c_backend.CListingArtifact.create(
            source_file,
            metadata_text=metadata_text,
            include_dir=str(c_backend._platform_include_dir_for_listing(source_file.platform_name, project_root)),
            project_root=project_root,
        )
    try:
        summary, summary_profile = artifact.summary_payload()
        total_rows = summary.get("total_rows", 0)
        payload, window_profile = artifact.window_payload(
            start=0,
            count=total_rows if isinstance(total_rows, int) else 0,
        )
        navigation, navigation_profile = artifact.navigation_payload()
        rows = list(payload["rows"])
        app_slot_analysis = navigation.get("app_slot_analysis")
        merged_profile = {**summary_profile, **navigation_profile, **window_profile}
        if isinstance(app_slot_analysis, dict):
            merged_profile["app_slot_analysis"] = app_slot_analysis
        return (
            rows,
            _api_calls_from_rows(rows),
            merged_profile,
        )
    finally:
        artifact.close()


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
        return {
            "analysis": analysis,
            "listing": {
                "rows": list(listing["rows"]),
                "app_slot_analysis": summary_profile.get("app_slot_analysis"),
                "type_flow_analysis": summary_profile.get("type_flow_analysis"),
            },
            "profile": cast(dict[str, object], {**summary_profile, **analysis_profile, **listing_profile}),
        }
    finally:
        artifact.close()
