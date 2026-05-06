from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from amiga_reversing.disasm import c_backend
from amiga_reversing.disasm.binary_source import BinarySource
from amiga_reversing.disasm.c_backend import ApiCallRowKey, api_calls_from_c_analysis, rows_from_c_listing_json
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.listing_types import ListingRow
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths


def build_project_rows_generation_with_c_backend(
    project_name: str,
    *,
    generation: str,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]]]:
    rows, api_calls, _ = build_project_rows_generation_with_c_backend_profile(
        project_name,
        generation=generation,
        project_root=project_root,
    )
    return rows, api_calls


def build_project_rows_generation_with_c_backend_profile(
    project_name: str,
    *,
    generation: str,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    if generation != "full":
        raise ValueError(f"Unsupported listing generation: {generation}")
    paths = resolve_project_paths(project_name, project_root=project_root)
    with effective_metadata_file(paths.target_dir) as metadata_path:
        metadata_text = c_backend._metadata_path_text(metadata_path)
        return build_project_rows_generation_from_source(
            paths.binary_source,
            metadata_text=metadata_text,
            generation=generation,
            project_root=project_root,
        )


def build_project_rows_generation_from_source(
    binary_source: BinarySource,
    *,
    metadata_text: str,
    generation: str,
    project_root: Path,
) -> tuple[list[ListingRow], dict[ApiCallRowKey, dict[str, object]], dict[str, object]]:
    if generation != "full":
        raise ValueError(f"Unsupported listing generation: {generation}")
    with c_backend._source_file_for_c_backend(binary_source, project_root=project_root) as source_file:
        include_dir = c_backend._platform_include_dir_for_listing(source_file.platform_name, project_root)
        if source_file.entry_offset is None:
            combined_text = c_backend._platform_file_text(
                "platform_file_facts_v2_listing_rows_with_analysis_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                metadata_text,
                str(include_dir),
                project_root=project_root,
            )
        else:
            combined_text = c_backend._platform_file_text(
                "platform_file_facts_v2_listing_rows_with_analysis_raw_path_json_alloc",
                source_file.platform_name,
                str(source_file.path),
                source_file.entry_offset,
                metadata_text,
                str(include_dir),
                project_root=project_root,
            )
    combined = cast(dict[str, object], json.loads(combined_text))
    listing_rows = cast(dict[str, object], combined.get("listing", {}))
    analysis = cast(dict[str, object], combined.get("analysis", {}))
    profile = cast(dict[str, object], combined.get("profile", {}))
    app_slot_analysis = listing_rows.get("app_slot_analysis")
    if isinstance(app_slot_analysis, dict):
        profile["app_slot_analysis"] = app_slot_analysis
    type_flow_analysis = listing_rows.get("type_flow_analysis")
    if isinstance(type_flow_analysis, dict):
        profile["type_flow_analysis"] = type_flow_analysis
    return rows_from_c_listing_json(listing_rows), api_calls_from_c_analysis(analysis), profile
