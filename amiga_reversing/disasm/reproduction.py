from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.binary_source import (
    BinarySource,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    RawBinarySource,
)
from amiga_reversing.disasm.c_backend import (
    FactsV2DirectRebuildRefused,
    FactsV2ProfiledOperationFailed,
    assemble_platform_source_text_with_c_backend,
    facts_v2_direct_rebuild_project_source_with_c_backend_profile,
    listing_artifact_source_text_with_c_backend_profile,
    reproduction_compare_rebuilt_bytes_with_c_backend_profile,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_hash,
)
from amiga_reversing.disasm.facts_v2_source_refusal import (
    FactsV2SourceRefused,
)
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    resolve_project_dir,
    resolve_project_paths,
)
from amiga_reversing.disasm.target_metadata import (
    TARGET_CORRECTIONS_FILE_NAME,
    TARGET_METADATA_FILE_NAME,
    TARGET_SEEDED_METADATA_FILE_NAME,
)
from amiga_reversing.disasm.target_ui_edits import TARGET_UI_EDITS_FILE_NAME

REPRODUCTION_FILE_NAME = "reproduction.json"
FACTS_V2_DIRECT_SOURCE_COMPARE_ENV = "AMIGA_REVERSING_FACTS_V2_DIRECT_SOURCE_COMPARE"
MAX_DIFF_RANGES = 128
MAX_DIAGNOSTICS = 80
REPRODUCTION_BACKENDS = {"auto", "amiga-hunk", "atari-st", "amiga-raw"}
REPRODUCTION_ANALYSIS_STAMP = "facts_v2"
REPRODUCTION_ASSEMBLERS = {"our"}
REPRODUCTION_ORACLE_MODES = {"vasm", "devpac"}
REPRODUCTION_CPUS = {"68000", "68010", "68020", "68030", "68040", "68060", "any"}
REPRODUCTION_MODES = {"exact", "template_preserved", "canonical", "content", "semantic"}
REPRODUCTION_CONTAINER_POLICIES = {"assembler_default", "preserve_original"}
REPRODUCTION_RELOCATION_POLICIES = {"assembler_default", "preserve_original_encoding"}
REPRODUCTION_COMPARISONS = {"full_file", "content", "semantic"}
REPRODUCTION_REQUESTED_EXACTNESS = {"full_file", "content"}
REPRODUCTION_REQUESTED_EXACTNESS_IDS = {"full_file": 1, "content": 2}
_ATARI_PRG_HEADER_SIZE = 28
_ATARI_PRG_MAGIC = 0x601A
_HUNK_TYPE_ID_MASK = 0x1FFFFFFF
_HUNK_SIZE_LONGS_MASK = 0x3FFFFFFF
_HUNK_MEM_SHIFT = 30
_HUNK_HEADER = 1011
_HUNK_CODE = 1001
_HUNK_DATA = 1002
_HUNK_BSS = 1003
_HUNK_SYMBOL = 1008
_HUNK_DEBUG = 1009
_HUNK_END = 1010
_HUNK_EXT = 1007
_HUNK_RELOC32 = 1004
_HUNK_RELOC32SHORT = 1020
_HUNK_SECTION_TYPES = {_HUNK_CODE, _HUNK_DATA, _HUNK_BSS}
_HUNK_RELOCATION_LONG_TYPES = {1004, 1005, 1006, 1015, 1016, 1017, 1021, 1022}
_HUNK_EXT_DEFINITION_TYPES = {0, 1, 2, 3}
_HUNK_EXT_REFERENCE_TYPES = {129, 131, 132, 133, 134, 135, 136, 138, 139}
_HUNK_EXT_COMMON_REFERENCE_TYPES = {130, 137}

_C_COMPARE_STATUS_LABELS = {
    0: "not_compared",
    1: "exact_file",
    2: "semantic_container_oddity",
    3: "mismatch",
    4: "invalid_comparison",
}
_C_COMPARE_EXACTNESS_LABELS = {
    0: "none",
    1: "full_file",
    2: "content",
    3: "mismatch",
}
_C_COMPARE_CONTENT_ISSUE_FLAGS = {
    1 << 0: "payload_mismatch",
    1 << 1: "relocation_semantic_mismatch",
    1 << 3: "size_mismatch",
}
_C_COMPARE_FILE_STRUCTURE_ISSUE_FLAGS = {
    1 << 2: "container_shape_mismatch",
    1 << 5: "hunk_relocation_order_mismatch",
    1 << 6: "hunk_relocation_group_mismatch",
    1 << 7: "hunk_relocation_encoding_mismatch",
    1 << 8: "policy_divergence",
    1 << 9: "unsupported_container_shape",
}
_C_COMPARE_FILE_STRUCTURE_ISSUE_BITS = {label: bit for bit, label in _C_COMPARE_FILE_STRUCTURE_ISSUE_FLAGS.items()}


def reproduction_report_path(target_dir: Path) -> Path:
    return target_dir / REPRODUCTION_FILE_NAME


def rebuilt_target_dir(target_name: str, *, project_root: Path = PROJECT_ROOT) -> Path:
    return project_root / "bin" / "rebuilt" / target_name


def run_reproduction(
    target_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
    assembler: str = "our",
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    profile: bool = False,
    pre_rendered_source_text: str | None = None,
    pre_rendered_source_profile: Mapping[str, object] | None = None,
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None = None,
    source_assembly_debug: bool = False,
) -> dict[str, object]:
    started_at = time.time()
    profile_started_at = time.perf_counter()
    profile_timings: dict[str, object] = {}
    out_dir = rebuilt_target_dir(target_name, project_root=project_root)
    source_path = out_dir / "source.s"
    rebuilt_path = out_dir / "rebuilt.bin"
    canonical_rebuilt_path = out_dir / "rebuilt.canonical.bin"
    target_dir: Path | None = None
    source_text: str | None = pre_rendered_source_text
    source_size = len(source_text.encode("utf-8")) if source_text is not None else 0
    rebuilt_bytes: bytes | None = None
    assembled_source_for_reproduction = False
    direct_rebuild_for_reproduction = False
    direct_source_report: dict[str, object] | None = None
    assembler_stdout = ""
    assembler_stderr = ""
    listing_profile: dict[str, object] | None = (
        dict(pre_rendered_source_profile) if pre_rendered_source_profile is not None else None
    )
    input_stamp = unresolved_reproduction_input_stamp(
        target_name,
        project_root=project_root,
        assembler=assembler,
        error="not prepared",
    )
    backend = "unknown"
    base_report = _base_reproduction_report(
        target_name,
        started_at=started_at,
        input_stamp=input_stamp,
        assembler=assembler,
        backend=backend,
        source_path=source_path,
        rebuilt_path=rebuilt_path,
    )

    phase = "prepare"
    try:
        _emit_progress(
            progress_callback,
            target_name=target_name,
            phase=phase,
            started_at=profile_started_at,
        )
        phase_started_at = time.perf_counter()
        paths = resolve_project_paths(target_name, project_root=project_root, require_entities=False)
        target_dir = paths.target_dir
        input_stamp = reproduction_input_stamp(target_name, project_root=project_root, assembler=assembler)
        backend = cast(str, input_stamp["backend"])
        assembler = cast(str, input_stamp["assembler"])
        assembler_cpu = cast(str, input_stamp["assembler_cpu"])
        base_report = _base_reproduction_report(
            target_name,
            started_at=started_at,
            input_stamp=input_stamp,
            assembler=assembler,
            backend=backend,
            source_path=source_path,
            rebuilt_path=rebuilt_path,
        )
        _record_profile_timing(profile_timings, "prepare_seconds", phase_started_at)
        out_dir.mkdir(parents=True, exist_ok=True)
        if assembler not in REPRODUCTION_ASSEMBLERS:
            report = {
                **base_report,
                "status": "tool_error",
                "tool_error": f"unsupported exactness assembler: {assembler}",
                "finished_at": time.time(),
                "issues": [_issue("tool", f"unsupported exactness assembler: {assembler}", None)],
            }
            return _write_reproduction_report(paths.target_dir, report)
        use_facts_v2_native_reproduction = source_text is None
        use_facts_v2_direct_rebuild = (
            use_facts_v2_native_reproduction
            and backend != "amiga-raw"
            and not source_assembly_debug
        )
        use_facts_v2_direct_compare = use_facts_v2_direct_rebuild
        use_listing_source_assembly = use_facts_v2_native_reproduction and not use_facts_v2_direct_rebuild
        if use_facts_v2_direct_rebuild:
            phase = "direct_rebuild"
            phase_started_at = time.perf_counter()
            _emit_progress(
                progress_callback,
                target_name=target_name,
                phase=phase,
                started_at=profile_started_at,
                backend=backend,
                assembler_tool_path=str(_platform_file_lib_path(project_root)),
            )
            with effective_metadata_file(paths.target_dir) as metadata_path:
                try:
                    direct_bytes, listing_profile, direct_profile = (
                        facts_v2_direct_rebuild_project_source_with_c_backend_profile(
                            paths.binary_source,
                            metadata_path=metadata_path,
                            output_path=rebuilt_path,
                            compare_original=use_facts_v2_direct_compare,
                            project_root=project_root,
                        )
                    )
                    rebuilt_bytes = direct_bytes
                    direct_rebuild_for_reproduction = True
                    _merge_direct_rebuild_profile(profile_timings, direct_profile)
                    _record_profile_timing(profile_timings, "direct_rebuild_seconds", phase_started_at)
                    profile_timings["render_seconds"] = _profile_timing_total(listing_profile)
                    profile_timings["assemble_seconds"] = 0.0
                    profile_timings["facts_v2_direct_rebuild_c_api"] = 1.0
                    source_size = _facts_v2_profile_source_bytes(listing_profile)
                    profile_timings["source_file_rewritten"] = 0.0
                    profile_timings["write_source_seconds"] = 0.0
                    if facts_v2_direct_source_compare_enabled():
                        include_dir = _include_dir_for_backend(backend, project_root)
                        compare_started_at = time.perf_counter()
                        rendered_source_text, source_compare_profile = (
                            listing_artifact_source_text_with_c_backend_profile(
                                paths.binary_source,
                                metadata_path=metadata_path,
                                project_root=project_root,
                            )
                        )
                        source_bytes, assembler_profile = assemble_platform_source_text_with_c_backend(
                            backend,
                            rendered_source_text,
                            include_dir=include_dir if include_dir is not None and include_dir.exists() else None,
                            target_cpu=assembler_cpu,
                            project_root=project_root,
                        )
                        if listing_profile is None:
                            listing_profile = source_compare_profile
                        _merge_assembler_profile(profile_timings, assembler_profile)
                        _record_profile_timing(
                            profile_timings,
                            "facts_v2_direct_source_compare_seconds",
                            compare_started_at,
                        )
                        original_for_source_compare = paths.binary_source.read_bytes()
                        source_compare_direct_profile = reproduction_compare_rebuilt_bytes_with_c_backend_profile(
                            paths.binary_source,
                            source_bytes,
                            metadata_path=metadata_path,
                            project_root=project_root,
                        )
                        _record_direct_source_comparison(
                            profile_timings,
                            direct_bytes,
                            source_bytes,
                            compare_profile=source_compare_direct_profile,
                        )
                        direct_source_report = _direct_source_report_fields(
                            original_for_source_compare,
                            source_bytes,
                            assembler=assembler,
                        )
                        if direct_bytes != source_bytes:
                            profile_timings["facts_v2_direct_source_mismatch"] = 1.0
                    if (
                        use_facts_v2_direct_compare
                        and not facts_v2_direct_source_compare_enabled()
                        and (
                            direct_profile.get("direct_rebuild_exact") is True
                            or direct_profile.get("direct_compare_semantic_exact") is True
                        )
                    ):
                        reproduction_policy = _input_reproduction_policy(input_stamp)
                        comparison = _direct_compare_reproduction_comparison(
                            backend, reproduction_policy, direct_profile
                        )
                        selected_exact = comparison["selected_exact"] is True
                        digest = _sha256_bytes(direct_bytes)
                        direct_full_exact = direct_profile.get("direct_rebuild_exact") is True
                        profile_timings["facts_v2_direct_exact_fast_path"] = 1.0 if direct_full_exact else 0.0
                        if not direct_full_exact:
                            profile_timings["facts_v2_direct_semantic_fast_path"] = 1.0
                        profile_timings["diff_phase_seconds"] = 0.0
                        original_size = _optional_int(input_stamp.get("original_size"), len(direct_bytes))
                        direct_shape_diagnostics = _direct_compare_shape_diagnostics(
                            direct_profile, row_for_section_offset
                        )
                        direct_shape_row_issues = _direct_compare_shape_row_issues(
                            direct_profile, row_for_section_offset
                        )
                        report = {
                            **base_report,
                            "status": "exact" if selected_exact else "binary_mismatch",
                            "exact": selected_exact,
                            "finished_at": time.time(),
                            "original_size": original_size,
                            "rebuilt_size": len(direct_bytes),
                            "rebuilt_sha256": digest,
                            "canonical_rebuilt_size": len(direct_bytes),
                            "canonical_rebuilt_sha256": digest,
                            "canonical_rebuilt_path": str(rebuilt_path),
                            "first_diff": None,
                            "diff_ranges": [],
                            "canonical_diff_ranges": [],
                            "file_layout": [],
                            "row_mappings": direct_shape_row_issues,
                            "issues": direct_shape_row_issues,
                            "assembler_diagnostics": [],
                            "assembler_stdout": assembler_stdout,
                            "assembler_stderr": assembler_stderr,
                            "file_shape_adjustments": [],
                            "file_shape_diagnostics": direct_shape_diagnostics,
                            "canonical_file_shape_diagnostics": [dict(item) for item in direct_shape_diagnostics],
                            "comparison": comparison,
                        }
                        if direct_source_report is not None:
                            report.update(direct_source_report)
                        if listing_profile is not None:
                            report["listing_profile"] = listing_profile
                        if profile:
                            report["profile"] = _profile_payload(profile_timings, profile_started_at)
                        return _write_reproduction_report(paths.target_dir, report)
                except FactsV2SourceRefused as exc:
                    message = str(exc)
                    _record_profile_timing(profile_timings, "direct_rebuild_seconds", phase_started_at)
                    profile_timings["render_seconds"] = _profile_timing_total(exc.listing_profile)
                    profile_timings["assemble_seconds"] = 0.0
                    profile_timings["facts_v2_direct_rebuild_c_api"] = 1.0
                    report = {
                        **base_report,
                        "status": "render_error",
                        "finished_at": time.time(),
                        "tool_error": message,
                        "issues": [_issue("renderer", message, None)],
                        "listing_profile": exc.listing_profile,
                    }
                    if profile:
                        report["profile"] = _profile_payload(profile_timings, profile_started_at)
                    return _write_reproduction_report(paths.target_dir, report)
                except FactsV2DirectRebuildRefused as exc:
                    listing_profile = exc.source_profile
                    _merge_direct_rebuild_profile(profile_timings, exc.direct_profile)
                    _record_profile_timing(profile_timings, "direct_rebuild_seconds", phase_started_at)
                    profile_timings["facts_v2_direct_rebuild_c_api"] = 1.0
                    message = f"facts_v2 direct rebuild refused: {exc}"
                    accepted_kind = _accepted_direct_rebuild_refusal_kind(
                        backend,
                        source_profile=listing_profile,
                        direct_profile=exc.direct_profile,
                    )
                    if accepted_kind is not None:
                        report = {
                            **base_report,
                            "status": "accepted_mismatch",
                            "accepted_mismatch_kind": accepted_kind,
                            "accepted_mismatch_reason": message,
                            "finished_at": time.time(),
                            "issues": [],
                            "listing_profile": listing_profile,
                            "direct_rebuild_profile": exc.direct_profile,
                        }
                        if profile:
                            report["profile"] = _profile_payload(profile_timings, profile_started_at)
                        return _write_reproduction_report(paths.target_dir, report)
                    report = {
                        **base_report,
                        "status": "tool_error",
                        "finished_at": time.time(),
                        "tool_error": message,
                        "issues": [_issue("direct_rebuild", message, None)],
                        "listing_profile": listing_profile,
                        "direct_rebuild_profile": exc.direct_profile,
                    }
                    if profile:
                        report["profile"] = _profile_payload(profile_timings, profile_started_at)
                    return _write_reproduction_report(paths.target_dir, report)
                except FactsV2ProfiledOperationFailed as exc:
                    listing_profile = exc.source_profile
                    _merge_direct_rebuild_profile(profile_timings, exc.operation_profile)
                    _record_profile_timing(profile_timings, "direct_rebuild_seconds", phase_started_at)
                    profile_timings["facts_v2_direct_rebuild_c_api"] = 1.0
                    message = str(exc)
                    report = {
                        **base_report,
                        "status": "tool_error",
                        "finished_at": time.time(),
                        "tool_error": message,
                        "issues": [_issue("direct_rebuild", message, None)],
                        "listing_profile": listing_profile,
                        "direct_rebuild_profile": exc.operation_profile,
                    }
                    if profile:
                        report["profile"] = _profile_payload(profile_timings, profile_started_at)
                    return _write_reproduction_report(paths.target_dir, report)
        if use_listing_source_assembly and rebuilt_bytes is None:
            phase = "render_source"
            phase_started_at = time.perf_counter()
            include_dir = _include_dir_for_backend(backend, project_root)
            _emit_progress(
                progress_callback,
                target_name=target_name,
                phase=phase,
                started_at=profile_started_at,
                backend=backend,
                assembler_tool_path=str(_platform_file_lib_path(project_root)),
            )
            with effective_metadata_file(paths.target_dir) as metadata_path:
                try:
                    rendered_source_text, listing_profile = listing_artifact_source_text_with_c_backend_profile(
                        paths.binary_source,
                        metadata_path=metadata_path,
                        project_root=project_root,
                    )
                except FactsV2SourceRefused as exc:
                    message = str(exc)
                    _record_profile_timing(profile_timings, "render_source_seconds", phase_started_at)
                    profile_timings["render_seconds"] = _profile_timing_total(exc.listing_profile)
                    profile_timings["assemble_seconds"] = 0.0
                    profile_timings["listing_artifact_source_assembly"] = 1.0
                    report = {
                        **base_report,
                        "status": "render_error",
                        "finished_at": time.time(),
                        "tool_error": message,
                        "issues": [_issue("renderer", message, None)],
                        "listing_profile": exc.listing_profile,
                    }
                    if profile:
                        report["profile"] = _profile_payload(profile_timings, profile_started_at)
                    return _write_reproduction_report(paths.target_dir, report)
                _record_profile_timing(profile_timings, "render_source_seconds", phase_started_at)
                profile_timings["render_seconds"] = _profile_timing_total(listing_profile)
                source_size = _facts_v2_profile_source_bytes(listing_profile)
                phase = "assemble"
                phase_started_at = time.perf_counter()
                try:
                    rebuilt_bytes, assembler_profile = assemble_platform_source_text_with_c_backend(
                        backend,
                        rendered_source_text,
                        include_dir=include_dir if include_dir is not None and include_dir.exists() else None,
                        output_path=rebuilt_path,
                        target_cpu=assembler_cpu,
                        project_root=project_root,
                    )
                    _merge_assembler_profile(profile_timings, assembler_profile)
                    assembled_source_for_reproduction = True
                except RuntimeError as exc:
                    assembler_stderr = str(exc)
                    _record_profile_timing(profile_timings, "assemble_seconds", phase_started_at)
                    profile_timings["listing_artifact_source_assembly"] = 1.0
                    diagnostics = parse_assembler_diagnostics(assembler_stderr)
                    report = {
                        **base_report,
                        "status": "assembler_error",
                        "finished_at": time.time(),
                        "assembler_diagnostics": diagnostics,
                        "assembler_stdout": assembler_stdout,
                        "assembler_stderr": assembler_stderr,
                        "issues": diagnostics or [_issue("assembler", "Assembler failed", None)],
                        "listing_profile": listing_profile,
                    }
                    if profile:
                        report["profile"] = _profile_payload(profile_timings, profile_started_at)
                    return _write_reproduction_report(paths.target_dir, report)
            _record_profile_timing(profile_timings, "assemble_seconds", phase_started_at)
            profile_timings["assemble_seconds"] = _flat_profile_total(assembler_profile)
            profile_timings["listing_artifact_source_assembly"] = 1.0
            profile_timings["source_file_rewritten"] = 0.0
            profile_timings["write_source_seconds"] = 0.0
        elif source_text is not None:
            profile_timings["render_seconds"] = (
                _profile_timing_total(listing_profile) if listing_profile is not None else 0.0
            )
            profile_timings["reused_source_text"] = 1.0
        if source_text is not None:
            source_size = len(source_text.encode("utf-8"))
        if source_text is not None:
            phase = "write_source"
            _emit_progress(
                progress_callback,
                target_name=target_name,
                phase=phase,
                started_at=profile_started_at,
                backend=backend,
                source_size=source_size,
            )
            source_size = _write_source_artifact(source_path, source_text, profile_timings)
        else:
            profile_timings["source_file_rewritten"] = 0.0
            profile_timings["write_source_seconds"] = 0.0

        if rebuilt_bytes is None:
            phase = "assemble"
            phase_started_at = time.perf_counter()
            include_dir = _include_dir_for_backend(backend, project_root)
            _emit_progress(
                progress_callback,
                target_name=target_name,
                phase=phase,
                started_at=profile_started_at,
                backend=backend,
                source_size=source_size,
                assembler_tool_path=str(_platform_file_lib_path(project_root)),
            )
            if source_text is None:
                raise RuntimeError("source text missing before assembly")
            try:
                rebuilt_bytes, assembler_profile = assemble_platform_source_text_with_c_backend(
                    backend,
                    source_text,
                    include_dir=include_dir if include_dir is not None and include_dir.exists() else None,
                    output_path=rebuilt_path,
                    target_cpu=assembler_cpu,
                    project_root=project_root,
                )
                _merge_assembler_profile(profile_timings, assembler_profile)
                assembled_source_for_reproduction = True
            except RuntimeError as exc:
                assembler_stderr = str(exc)
                _record_profile_timing(profile_timings, "assemble_seconds", phase_started_at)
                diagnostics = parse_assembler_diagnostics(assembler_stderr)
                report = {
                    **base_report,
                    "status": "assembler_error",
                    "finished_at": time.time(),
                    "assembler_diagnostics": diagnostics,
                    "assembler_stdout": assembler_stdout,
                    "assembler_stderr": assembler_stderr,
                    "issues": diagnostics or [_issue("assembler", "Assembler failed", None)],
                }
                if profile:
                    report["profile"] = _profile_payload(profile_timings, profile_started_at)
                return _write_reproduction_report(paths.target_dir, report)
            _record_profile_timing(profile_timings, "assemble_seconds", phase_started_at)
        diagnostics = parse_assembler_diagnostics(assembler_stdout + "\n" + assembler_stderr)

        phase = "diff"
        phase_started_at = time.perf_counter()
        rebuilt_size = len(rebuilt_bytes)
        _emit_progress(
            progress_callback,
            target_name=target_name,
            phase=phase,
            started_at=profile_started_at,
            backend=backend,
            source_size=source_size,
            rebuilt_size=rebuilt_size,
        )
        read_original_started_at = time.perf_counter()
        original = paths.binary_source.read_bytes()
        _record_profile_timing(profile_timings, "read_original_seconds", read_original_started_at)
        canonical_rebuilt = rebuilt_bytes
        profile_timings["read_rebuilt_seconds"] = 0.0
        profile_timings["reused_assembler_rebuilt_bytes"] = 1.0
        policy_started_at = time.perf_counter()
        reproduction_policy = _input_reproduction_policy(input_stamp)
        if direct_rebuild_for_reproduction:
            rebuilt = canonical_rebuilt
            file_shape_adjustments: list[dict[str, object]] = []
        else:
            rebuilt, file_shape_adjustments = apply_reproduction_output_policy(
                original,
                canonical_rebuilt,
                backend=backend,
                policy=reproduction_policy,
            )
        _record_profile_timing(profile_timings, "file_shape_policy_seconds", policy_started_at)
        diff_started_at = time.perf_counter()
        diff_ranges = grouped_diff_ranges(original, rebuilt)
        canonical_diff_ranges = (
            diff_ranges
            if not file_shape_adjustments or rebuilt is canonical_rebuilt
            else grouped_diff_ranges(original, canonical_rebuilt)
        )
        first_diff_payload = _first_diff_from_ranges(original, rebuilt, diff_ranges)
        _record_profile_timing(profile_timings, "diff_seconds", diff_started_at)
        if not diff_ranges and not canonical_diff_ranges:
            file_layout: list[dict[str, object]] = []
            row_issues: list[dict[str, object]] = []
            file_shape_diagnostics: list[dict[str, object]] = []
            canonical_file_shape_diagnostics: list[dict[str, object]] = []
            profile_timings["file_layout_seconds"] = 0.0
            profile_timings["row_mapping_seconds"] = 0.0
            comparison, c_compare_profile = _comparison_for_rebuilt_bytes(
                paths.binary_source,
                rebuilt,
                backend=backend,
                policy=reproduction_policy,
                metadata_path=None,
                project_root=project_root,
                original=original,
                canonical_rebuilt=canonical_rebuilt,
                diff_ranges=diff_ranges,
                canonical_diff_ranges=canonical_diff_ranges,
                file_layout=file_layout,
            )
            if c_compare_profile is not None:
                _merge_source_compare_profile(profile_timings, c_compare_profile)
        else:
            layout_started_at = time.perf_counter()
            file_layout = file_layout_for_binary_source(paths.binary_source, backend=backend, data=original)
            _record_profile_timing(profile_timings, "file_layout_seconds", layout_started_at)
            row_mapping_started_at = time.perf_counter()
            row_issues = diff_issues_for_lookup(
                diff_ranges,
                row_for_section_offset,
                file_layout=file_layout,
            )
            _record_profile_timing(profile_timings, "row_mapping_seconds", row_mapping_started_at)
            file_shape_diagnostics = file_shape_diagnostics_for_mismatch(
                original,
                rebuilt,
                backend=backend,
                diff_ranges=diff_ranges,
                file_layout=file_layout,
            )
            canonical_file_shape_diagnostics = file_shape_diagnostics_for_mismatch(
                original,
                canonical_rebuilt,
                backend=backend,
                diff_ranges=canonical_diff_ranges,
                file_layout=file_layout,
            )
            comparison, c_compare_profile = _comparison_for_rebuilt_bytes(
                paths.binary_source,
                rebuilt,
                backend=backend,
                policy=reproduction_policy,
                metadata_path=None,
                project_root=project_root,
                original=original,
                canonical_rebuilt=canonical_rebuilt,
                diff_ranges=diff_ranges,
                canonical_diff_ranges=canonical_diff_ranges,
                file_layout=file_layout,
            )
            if c_compare_profile is not None:
                _merge_source_compare_profile(profile_timings, c_compare_profile)
                direct_shape_diagnostics = _direct_compare_shape_diagnostics(
                    c_compare_profile, row_for_section_offset
                )
                if direct_shape_diagnostics:
                    file_shape_diagnostics = direct_shape_diagnostics
                    canonical_file_shape_diagnostics = [dict(item) for item in direct_shape_diagnostics]
        if direct_source_report is None and assembled_source_for_reproduction:
            direct_source_report = _direct_source_report_fields_from_ranges(
                original,
                canonical_rebuilt,
                assembler=assembler,
                diff_ranges=canonical_diff_ranges,
            )
        _record_profile_timing(profile_timings, "diff_phase_seconds", phase_started_at)
        exact = bool(comparison.get("full_file_exact"))
        report_status = "exact" if exact else "binary_mismatch"
        comparison_status = comparison.get("status")
        if (
            comparison_status in {"content_match", "semantic_match"}
            and reproduction_policy.get("comparison") in {"content", "semantic"}
        ):
            report_status = str(comparison_status)
        if rebuilt != canonical_rebuilt:
            canonical_rebuilt_path.write_bytes(canonical_rebuilt)
            rebuilt_path.write_bytes(rebuilt)
        canonical_path_for_report = canonical_rebuilt_path if rebuilt != canonical_rebuilt else rebuilt_path
        report = {
            **base_report,
            "status": report_status,
            "exact": exact,
            "finished_at": time.time(),
            "original_size": len(original),
            "rebuilt_size": len(rebuilt),
            "rebuilt_sha256": _sha256_bytes(rebuilt),
            "canonical_rebuilt_size": len(canonical_rebuilt),
            "canonical_rebuilt_sha256": _sha256_bytes(canonical_rebuilt),
            "canonical_rebuilt_path": str(canonical_path_for_report),
            "first_diff": first_diff_payload,
            "diff_ranges": diff_ranges,
            "canonical_diff_ranges": canonical_diff_ranges,
            "file_layout": file_layout,
            "row_mappings": row_issues,
            "issues": row_issues,
            "assembler_diagnostics": diagnostics,
            "assembler_stdout": assembler_stdout,
            "assembler_stderr": assembler_stderr,
            "file_shape_adjustments": file_shape_adjustments,
            "file_shape_diagnostics": file_shape_diagnostics,
            "canonical_file_shape_diagnostics": canonical_file_shape_diagnostics,
            "comparison": comparison,
        }
        if direct_source_report is not None:
            report.update(direct_source_report)
        if listing_profile is not None:
            report["listing_profile"] = listing_profile
        if profile:
            report["profile"] = _profile_payload(profile_timings, profile_started_at)
        _emit_progress(
            progress_callback,
            target_name=target_name,
            phase="done",
            started_at=profile_started_at,
            backend=backend,
            source_size=source_size,
            rebuilt_size=len(rebuilt),
            original_size=len(original),
            status=report["status"],
        )
        return _write_reproduction_report(paths.target_dir, report)
    except Exception as exc:
        if target_dir is None:
            target_dir = _best_effort_target_dir(target_name, project_root=project_root)
        if "stamp_error" not in input_stamp or input_stamp.get("stamp_error") == "not prepared":
            input_stamp = unresolved_reproduction_input_stamp(
                target_name,
                project_root=project_root,
                assembler=assembler,
                error=str(exc),
                target_dir=target_dir,
            )
            base_report = _base_reproduction_report(
                target_name,
                started_at=started_at,
                input_stamp=input_stamp,
                assembler=assembler,
                backend=str(input_stamp.get("backend") or backend),
                source_path=source_path,
                rebuilt_path=rebuilt_path,
            )
        status = "render_error" if phase == "render" else "tool_error"
        issue_kind = "renderer" if phase == "render" else "tool"
        report = {
            **base_report,
            "status": status,
            "finished_at": time.time(),
            "tool_error": str(exc),
            "issues": [_issue(issue_kind, str(exc), None)],
        }
        if profile:
            report["profile"] = _profile_payload(profile_timings, profile_started_at)
        if target_dir is None:
            return report
        return _write_reproduction_report(target_dir, report)


def load_reproduction_report(
    target_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    resolve_error: Exception | None = None
    target_dir: Path | None = None
    try:
        paths = resolve_project_paths(target_name, project_root=project_root, require_entities=False)
        target_dir = paths.target_dir
    except Exception as exc:
        resolve_error = exc
        target_dir = _best_effort_target_dir(target_name, project_root=project_root)
        if target_dir is None:
            raise
    assert target_dir is not None
    path = reproduction_report_path(target_dir)
    if not path.exists():
        try:
            input_stamp = reproduction_input_stamp(target_name, project_root=project_root)
        except Exception as exc:
            input_stamp = unresolved_reproduction_input_stamp(
                target_name,
                project_root=project_root,
                assembler="our",
                error=str(resolve_error or exc),
                target_dir=target_dir,
            )
        return {
            "target": target_name,
            "status": "not_ready",
            "exact": False,
            "stale": False,
            "issues": [],
            "diff_ranges": [],
            "row_mappings": [],
            "assembler_diagnostics": [],
            "input_stamp": input_stamp,
        }
    payload = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    assembler = str(payload.get("assembler") or "our")
    try:
        current_stamp = reproduction_input_stamp(
            target_name,
            project_root=project_root,
            assembler=assembler,
        )
    except Exception as exc:
        current_stamp = unresolved_reproduction_input_stamp(
            target_name,
            project_root=project_root,
            assembler=assembler,
            error=str(exc),
            target_dir=target_dir,
        )
    stale = payload.get("input_stamp") != current_stamp
    return {**payload, "stale": stale, "current_input_stamp": current_stamp}


def reproduction_input_stamp(
    target_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
    assembler: str = "our",
) -> dict[str, object]:
    paths = resolve_project_paths(target_name, project_root=project_root, require_entities=False)
    options = reproduction_options_for_target(paths.target_dir)
    backend = _effective_reproduction_backend(backend_for_binary_source(paths.binary_source), options)
    assembler = _effective_reproduction_assembler(assembler, options)
    assembler_cpu = _effective_reproduction_cpu(options)
    reproduction_policy = reproduction_policy_for_options(options)
    assembler_path = _platform_file_lib_path(project_root)
    assembler_stamp = _file_stamp(assembler_path)
    tool_path = str(assembler_path)
    original = paths.binary_source.read_bytes()
    return {
        "original_sha256": _sha256_bytes(original),
        "original_size": len(original),
        "effective_metadata_sha256": effective_metadata_hash(paths.target_dir),
        "source_renderer": "c-backend",
        "analysis_backend": REPRODUCTION_ANALYSIS_STAMP,
        "source_renderer_tool_stamps": source_renderer_tool_stamps(project_root),
        "assembler": assembler,
        "assembler_cpu": assembler_cpu,
        "assembler_tool_path": tool_path,
        "assembler_tool_stamp": assembler_stamp,
        "backend": backend,
        "reproduction_options": options,
        "reproduction_policy": reproduction_policy,
    }


def reproduction_options_for_target(target_dir: Path) -> dict[str, object]:
    options = _default_reproduction_options()
    for reproduction_payload in _reproduction_option_payloads(target_dir):
        _merge_reproduction_options(options, reproduction_payload)
    return options


def unresolved_reproduction_input_stamp(
    target_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
    assembler: str = "our",
    error: str,
    target_dir: Path | None = None,
) -> dict[str, object]:
    options = _default_reproduction_options()
    if target_dir is not None:
        options = reproduction_options_for_target(target_dir)
    assembler = _effective_reproduction_assembler(assembler, options)
    reproduction_policy = reproduction_policy_for_options(options)
    return {
        "target": target_name,
        "original_sha256": None,
        "original_size": None,
        "effective_metadata_sha256": None
        if target_dir is None
        else _best_effort_effective_metadata_hash(target_dir),
        "source_renderer": "c-backend",
        "analysis_backend": REPRODUCTION_ANALYSIS_STAMP,
        "source_renderer_tool_stamps": source_renderer_tool_stamps(project_root),
        "assembler": assembler,
        "assembler_cpu": _effective_reproduction_cpu(options),
        "assembler_tool_path": str(_platform_file_lib_path(project_root)),
        "assembler_tool_stamp": _file_stamp(_platform_file_lib_path(project_root)),
        "backend": str(options.get("backend") or "unknown"),
        "reproduction_options": options,
        "reproduction_policy": reproduction_policy,
        "stamp_error": error,
    }


def _input_reproduction_policy(input_stamp: dict[str, object]) -> dict[str, object]:
    policy = input_stamp.get("reproduction_policy")
    if isinstance(policy, dict):
        return cast(dict[str, object], policy)
    options = input_stamp.get("reproduction_options")
    if isinstance(options, dict):
        return reproduction_policy_for_options(cast(dict[str, object], options))
    return reproduction_policy_for_options(_default_reproduction_options())


def backend_for_binary_source(binary_source: BinarySource) -> str:
    if isinstance(binary_source, RawBinarySource):
        return "amiga-raw"
    if isinstance(binary_source, HunkFileBinarySource):
        if binary_source.path.suffix.lower() in {".prg", ".tos", ".ttp"}:
            return "atari-st"
        return "amiga-hunk"
    if isinstance(binary_source, DiskEntryBinarySource):
        if binary_source.adf_path.suffix.lower() in {".st", ".msa"}:
            return "atari-st"
        return "amiga-hunk"
    raise ValueError(f"Unsupported binary source: {binary_source!r}")


def apply_reproduction_output_policy(
    original: bytes,
    rebuilt: bytes,
    *,
    backend: str,
    policy: dict[str, object],
) -> tuple[bytes, list[dict[str, object]]]:
    del original, backend, policy
    return rebuilt, []


def reproduction_comparison_result(
    original: bytes,
    canonical_rebuilt: bytes,
    compared_rebuilt: bytes,
    *,
    backend: str,
    policy: dict[str, object],
    diff_ranges: list[dict[str, object]],
    canonical_diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> dict[str, object]:
    full_file_exact = original == compared_rebuilt
    canonical_full_file_exact = original == canonical_rebuilt
    comparison_mode = str(policy.get("comparison") or "full_file")
    requested_exactness = str(policy.get("requested_exactness") or "full_file")
    requested_exactness_id = _direct_profile_int(policy, "requested_exactness_id") or 1
    if full_file_exact and canonical_full_file_exact:
        return {
            "mode": policy.get("mode"),
            "comparison": comparison_mode,
            "requested_exactness": requested_exactness,
            "requested_exactness_id": requested_exactness_id,
            "status": "exact_file",
            "selected_exact": True,
            "full_file_exact": True,
            "policy_adjusted_full_file_exact": True,
            "canonical_full_file_exact": True,
            "content_exact": True,
            "content_exact_accepted": requested_exactness_id >= 2,
            "content_exact_unaccepted": False,
            "payload_exact": True,
            "payload_diagnostics": [],
            "relocation_semantics_exact": True if backend == "amiga-hunk" else None,
            "relocation_encoding_exact": True if backend == "amiga-hunk" else None,
            "semantic_diagnostics": [],
            "failure_kinds": [],
            "diff_range_count": len(diff_ranges),
            "canonical_diff_range_count": len(canonical_diff_ranges),
        }
    payload_comparison = {"exact": original == canonical_rebuilt, "diagnostics": []}
    relocation_semantics = None
    relocation_encoding = None
    semantic_diagnostics: list[dict[str, object]] = []
    content_exact = bool(payload_comparison["exact"])
    content_exact_accepted = bool(content_exact and requested_exactness_id >= 2)
    policy_adjusted_full_file_exact = full_file_exact
    selected_exact = full_file_exact
    status = "exact_file" if full_file_exact else "mismatch"
    if content_exact_accepted:
        selected_exact = content_exact
        if content_exact and not full_file_exact:
            status = "accepted_content_exact"
    elif content_exact and not full_file_exact:
        status = "container_shape_mismatch"
    failure_kinds = _comparison_failure_kinds(
        payload_exact=bool(payload_comparison["exact"]),
        relocation_semantics=relocation_semantics,
        relocation_encoding=relocation_encoding,
        diff_ranges=diff_ranges,
        file_layout=file_layout,
    )
    return {
        "mode": policy.get("mode"),
        "comparison": comparison_mode,
        "requested_exactness": requested_exactness,
        "requested_exactness_id": requested_exactness_id,
        "status": status,
        "selected_exact": selected_exact,
        "full_file_exact": full_file_exact,
        "policy_adjusted_full_file_exact": policy_adjusted_full_file_exact,
        "canonical_full_file_exact": canonical_full_file_exact,
        "content_exact": content_exact,
        "content_exact_accepted": content_exact_accepted,
        "content_exact_unaccepted": bool(content_exact and not full_file_exact and not content_exact_accepted),
        "payload_exact": bool(payload_comparison["exact"]),
        "payload_diagnostics": payload_comparison["diagnostics"],
        "relocation_semantics_exact": relocation_semantics,
        "relocation_encoding_exact": relocation_encoding,
        "semantic_diagnostics": semantic_diagnostics,
        "failure_kinds": failure_kinds,
        "diff_range_count": len(diff_ranges),
        "canonical_diff_range_count": len(canonical_diff_ranges),
    }


def _direct_compare_reproduction_comparison(
    backend: str,
    policy: dict[str, object],
    direct_profile: dict[str, object],
) -> dict[str, object]:
    comparison_mode = str(policy.get("comparison") or "full_file")
    requested_exactness = str(policy.get("requested_exactness") or "full_file")
    requested_exactness_id = _direct_profile_int(policy, "requested_exactness_id") or 1
    status_id = _direct_profile_int(direct_profile, "direct_compare_status_id")
    exactness_id = _direct_profile_int(direct_profile, "direct_compare_exactness_id")
    issue_flags = _direct_profile_int(direct_profile, "direct_compare_issue_group_flags") or 0
    full_file_exact = bool(exactness_id == 1 or direct_profile.get("direct_rebuild_exact") is True)
    semantic_exact = bool(exactness_id in {1, 2} or direct_profile.get("direct_compare_semantic_exact") is True)
    content_exact_accepted = bool(semantic_exact and requested_exactness_id >= 2)
    selected_exact = bool(full_file_exact or content_exact_accepted)
    payload_exact = bool(semantic_exact or direct_profile.get("direct_compare_payload_exact") is True)
    relocation_semantics = None
    if backend in {"amiga-hunk", "atari-st"}:
        relocation_semantics = bool(semantic_exact and not (issue_flags & (1 << 1)))
    status = _C_COMPARE_STATUS_LABELS.get(status_id or -1)
    if status is None:
        status = "exact_file" if full_file_exact else "semantic_container_oddity"
    content_issue_kinds = _c_compare_issue_labels(issue_flags, _C_COMPARE_CONTENT_ISSUE_FLAGS)
    file_structure_issue_kinds = _c_compare_issue_labels(issue_flags, _C_COMPARE_FILE_STRUCTURE_ISSUE_FLAGS)
    failure_kinds = [] if full_file_exact else content_issue_kinds + file_structure_issue_kinds
    return {
        "mode": policy.get("mode"),
        "comparison": comparison_mode,
        "requested_exactness": requested_exactness,
        "requested_exactness_id": requested_exactness_id,
        "status": status,
        "selected_exact": selected_exact,
        "full_file_exact": full_file_exact,
        "policy_adjusted_full_file_exact": selected_exact,
        "canonical_full_file_exact": full_file_exact,
        "content_exact": bool(full_file_exact or semantic_exact),
        "content_exact_accepted": content_exact_accepted,
        "content_exact_unaccepted": bool(semantic_exact and not full_file_exact and not content_exact_accepted),
        "payload_exact": bool(full_file_exact or payload_exact),
        "payload_diagnostics": [],
        "relocation_semantics_exact": True
        if full_file_exact and backend in {"amiga-hunk", "atari-st"}
        else bool(relocation_semantics),
        "relocation_encoding_exact": bool(full_file_exact and backend in {"amiga-hunk", "atari-st"}),
        "semantic_diagnostics": _direct_compare_issue_diagnostics(content_issue_kinds, "content"),
        "failure_kinds": failure_kinds,
        "content_issue_kinds": content_issue_kinds,
        "file_structure_issue_kinds": file_structure_issue_kinds,
        "diff_range_count": 0,
        "canonical_diff_range_count": 0 if full_file_exact else None,
        "direct_compare_status": status,
        "direct_compare_exactness": _C_COMPARE_EXACTNESS_LABELS.get(exactness_id or -1, "unknown"),
    }


def _direct_profile_int(profile: dict[str, object], key: str) -> int | None:
    value = profile.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _c_compare_issue_labels(flags: int, labels_by_flag: dict[int, str]) -> list[str]:
    return [label for bit, label in labels_by_flag.items() if flags & bit]


def _direct_compare_issue_diagnostics(issue_kinds: list[str], group: str) -> list[dict[str, object]]:
    return [{"kind": issue_kind, "group": group, "source": "facts_v2_direct_compare"} for issue_kind in issue_kinds]


def _direct_compare_shape_diagnostics(
    direct_profile: dict[str, object],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None = None,
) -> list[dict[str, object]]:
    issue_flags = _direct_profile_int(direct_profile, "direct_compare_issue_group_flags") or 0
    issue_kinds = _c_compare_issue_labels(issue_flags, _C_COMPARE_FILE_STRUCTURE_ISSUE_FLAGS)
    if issue_kinds:
        diagnostics = _direct_compare_issue_diagnostics(issue_kinds, "original_file_structure")
        _attach_direct_compare_source_hints(diagnostics, direct_profile, row_for_section_offset)
        return diagnostics
    if direct_profile.get("direct_compare_container_oddity") is not True:
        return []
    return [
        {
            "kind": "container_shape_oddity",
            "source": "facts_v2_direct_compare",
            "status": direct_profile.get("direct_compare_status") or "semantic_container_oddity",
        }
    ]


def _attach_direct_compare_source_hints(
    diagnostics: list[dict[str, object]],
    direct_profile: dict[str, object],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
) -> None:
    if row_for_section_offset is None:
        return
    hints = direct_profile.get("direct_compare_source_hints")
    if not isinstance(hints, list):
        return
    for diagnostic in diagnostics:
        bit = _C_COMPARE_FILE_STRUCTURE_ISSUE_BITS.get(str(diagnostic.get("kind") or ""))
        if bit is None:
            continue
        for hint in hints:
            if not isinstance(hint, dict):
                continue
            flags = _direct_profile_int(hint, "issue_group_flags") or 0
            section_index = _direct_profile_int(hint, "section_index")
            offset = _direct_profile_int(hint, "offset")
            if not (flags & bit) or section_index is None or offset is None:
                continue
            row_ref = _row_ref_for_lookup(row_for_section_offset, section_index, offset)
            if row_ref is None:
                continue
            row_index, row = row_ref
            diagnostic["row_index"] = row_index
            diagnostic["section_index"] = section_index
            diagnostic["section_offset"] = offset
            diagnostic["addr"] = _row_int(row, "addr")
            diagnostic["stable_key"] = _row_str(row, "stable_key")
            diagnostic["match_text"] = _row_match_text(row)
            break


def _direct_compare_shape_row_issues(
    direct_profile: dict[str, object],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for diagnostic in _direct_compare_shape_diagnostics(direct_profile, row_for_section_offset):
        if not isinstance(diagnostic.get("row_index"), int):
            continue
        row_ref = _row_ref_for_lookup(
            row_for_section_offset,
            _optional_int(diagnostic.get("section_index"), 0),
            _optional_int(diagnostic.get("section_offset"), 0),
        )
        issues.append(
            _issue(
                str(diagnostic.get("kind") or "file_structure"),
                str(diagnostic.get("kind") or "file structure issue"),
                row_ref,
                section_index=_optional_int(diagnostic.get("section_index"), 0),
                section_offset=_optional_int(diagnostic.get("section_offset"), 0),
            )
        )
    return issues


def _comparison_for_rebuilt_bytes(
    binary_source: BinarySource,
    rebuilt: bytes,
    *,
    backend: str,
    policy: dict[str, object],
    metadata_path: Path | None,
    project_root: Path,
    original: bytes,
    canonical_rebuilt: bytes,
    diff_ranges: list[dict[str, object]],
    canonical_diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> tuple[dict[str, object], dict[str, object] | None]:
    if backend != "amiga-raw":
        direct_profile = reproduction_compare_rebuilt_bytes_with_c_backend_profile(
            binary_source,
            rebuilt,
            metadata_path=metadata_path,
            project_root=project_root,
        )
        return _direct_compare_reproduction_comparison(backend, policy, direct_profile), direct_profile
    return (
        reproduction_comparison_result(
            original,
            canonical_rebuilt,
            rebuilt,
            backend=backend,
            policy=policy,
            diff_ranges=diff_ranges,
            canonical_diff_ranges=canonical_diff_ranges,
            file_layout=file_layout,
        ),
        None,
    )


def _merge_source_compare_profile(timings: dict[str, object], profile: dict[str, object]) -> None:
    for key, value in profile.items():
        if key.startswith("direct_compare_"):
            output_key = f"facts_v2_source_{key}"
        elif key.startswith("direct_rebuild_"):
            continue
        else:
            output_key = f"facts_v2_source_compare_{key}"
        if isinstance(value, bool):
            timings[output_key] = 1.0 if value else 0.0
        elif isinstance(value, (int, float)):
            timings[output_key] = round(float(value), 6)
        elif isinstance(value, str) and value:
            timings[output_key] = value


def file_shape_diagnostics_for_mismatch(
    original: bytes,
    rebuilt: bytes,
    *,
    backend: str,
    diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not diff_ranges:
        return []
    first_layout_kind = _first_diff_layout_kind(diff_ranges, file_layout)
    if backend == "atari-st" and first_layout_kind in {"header", "relocation", "symbol_table"}:
        return compare_atari_st_file_shape(original, rebuilt)
    return []


def compare_atari_st_file_shape(original: bytes, rebuilt: bytes) -> list[dict[str, object]]:
    original_header = _atari_st_header_fields(original)
    rebuilt_header = _atari_st_header_fields(rebuilt)
    if original_header is None or rebuilt_header is None:
        return [{"kind": "atari_header_parse_error"}]
    diagnostics: list[dict[str, object]] = []
    for key, original_value in original_header.items():
        rebuilt_value = rebuilt_header.get(key)
        if original_value != rebuilt_value:
            diagnostics.append(
                {
                    "kind": "atari_header_field_mismatch",
                    "field": key,
                    "original": original_value,
                    "rebuilt": rebuilt_value,
                }
            )
    original_reloc_size = max(0, len(original) - _atari_st_relocation_offset(original))
    rebuilt_reloc_size = max(0, len(rebuilt) - _atari_st_relocation_offset(rebuilt))
    if original_reloc_size != rebuilt_reloc_size:
        diagnostics.append(
            {
                "kind": "atari_relocation_size_mismatch",
                "original": original_reloc_size,
                "rebuilt": rebuilt_reloc_size,
            }
        )
    return diagnostics[:MAX_DIAGNOSTICS]


def file_layout_for_binary_source(
    binary_source: BinarySource,
    *,
    backend: str,
    data: bytes | None = None,
) -> list[dict[str, object]]:
    payload = binary_source.read_bytes() if data is None else data
    if backend == "atari-st":
        return _atari_st_file_layout(payload)
    if backend == "amiga-hunk":
        return _amiga_hunk_file_layout(payload)
    if backend.endswith("-raw"):
        start = 0
        if isinstance(binary_source, RawBinarySource):
            start = binary_source.code_start_offset
        layout: list[dict[str, object]] = []
        _append_layout_range(
            layout,
            "section_payload",
            start,
            len(payload),
            data_len=len(payload),
            section_index=0,
            hunk=0,
            section_offset_start=0,
            label="raw payload",
        )
        return layout
    return []


def first_diff(original: bytes, rebuilt: bytes) -> dict[str, object] | None:
    limit = min(len(original), len(rebuilt))
    for index in range(limit):
        if original[index] != rebuilt[index]:
            return {
                "offset": index,
                "original": original[index],
                "rebuilt": rebuilt[index],
            }
    if len(original) != len(rebuilt):
        return {
            "offset": limit,
            "original": None if limit >= len(original) else original[limit],
            "rebuilt": None if limit >= len(rebuilt) else rebuilt[limit],
        }
    return None


def _first_diff_from_ranges(
    original: bytes,
    rebuilt: bytes,
    diff_ranges: list[dict[str, object]],
) -> dict[str, object] | None:
    if not diff_ranges:
        return None
    offset = _required_int(diff_ranges[0].get("start"))
    return {
        "offset": offset,
        "original": None if offset >= len(original) else original[offset],
        "rebuilt": None if offset >= len(rebuilt) else rebuilt[offset],
    }


def grouped_diff_ranges(
    original: bytes,
    rebuilt: bytes,
    *,
    max_ranges: int = MAX_DIFF_RANGES,
) -> list[dict[str, object]]:
    if original == rebuilt:
        return []
    ranges: list[dict[str, object]] = []
    current_start: int | None = None
    current_end: int | None = None
    max_len = max(len(original), len(rebuilt))
    for offset in range(max_len):
        original_value = original[offset] if offset < len(original) else None
        rebuilt_value = rebuilt[offset] if offset < len(rebuilt) else None
        if original_value == rebuilt_value:
            if current_start is not None and current_end is not None:
                ranges.append(_diff_range(current_start, current_end, original, rebuilt))
                if len(ranges) >= max_ranges:
                    return ranges
                current_start = None
                current_end = None
            continue
        if current_start is None:
            current_start = offset
        current_end = offset + 1
    if current_start is not None and current_end is not None and len(ranges) < max_ranges:
        ranges.append(_diff_range(current_start, current_end, original, rebuilt))
    return ranges


def diff_issues_for_lookup(
    diff_ranges: list[dict[str, object]],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
    *,
    file_layout: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for diff_range in diff_ranges:
        if not file_layout:
            row = _row_ref_for_lookup(row_for_section_offset, None, _required_int(diff_range.get("start")))
            issues.append(_issue("diff", _diff_summary(diff_range), row, diff_range=diff_range))
            continue
        for issue_range, layout_range in _split_diff_range_by_layout(diff_range, file_layout):
            section_index = _layout_int(layout_range, "section_index")
            hunk = _layout_int(layout_range, "hunk")
            section_offset: int | None = None
            row = None
            layout_kind = str(layout_range.get("kind") or "file") if layout_range is not None else "file"
            issue_kind = f"diff_{layout_kind}"
            if layout_kind == "section_payload" and layout_range is not None:
                file_start = _required_int(layout_range.get("file_start"))
                section_offset_start = _required_int(layout_range.get("section_offset_start") or 0)
                section_offset = section_offset_start + _required_int(issue_range.get("start")) - file_start
                row = _row_ref_for_lookup(row_for_section_offset, section_index, section_offset)
                issue_kind = "diff" if row is not None else "diff_payload"
            issues.append(
                _issue(
                    issue_kind.replace("-", "_"),
                    _diff_summary(issue_range, layout_range=layout_range, section_offset=section_offset),
                    row,
                    diff_range=issue_range,
                    layout_range=layout_range,
                    section_index=section_index,
                    section_offset=section_offset,
                    hunk=hunk,
                )
            )
    return issues


def _row_ref_for_lookup(
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
    section_index: int | None,
    offset: int,
) -> tuple[int, Mapping[str, object]] | None:
    if row_for_section_offset is None:
        return None
    row = row_for_section_offset(section_index, offset)
    if row is None:
        return None
    row_index = _row_int(row, "row_index")
    if row_index is None:
        return None
    return row_index, row


def parse_assembler_diagnostics(
    text: str,
    *,
    rows: Sequence[Mapping[str, object]] | None = None,
) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.search(r"(?:(?:line|:)\s*)(\d+)", stripped, re.IGNORECASE)
        row = None
        if match and rows:
            line_no = int(match.group(1))
            if 1 <= line_no <= len(rows):
                row = (line_no - 1, rows[line_no - 1])
        diagnostics.append(_issue("assembler", stripped, row))
        if len(diagnostics) >= MAX_DIAGNOSTICS:
            break
    return diagnostics


def reproduction_navigation_entries(report: dict[str, object]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for issue_index, issue in enumerate(_dict_list(report.get("issues"))):
        addr = issue.get("addr")
        row_index = issue.get("row_index")
        if not isinstance(addr, int) or not isinstance(row_index, int):
            continue
        summary = issue.get("summary") or issue.get("message") or issue.get("kind") or "Repro issue"
        entries.append(
            {
                "addr": addr,
                "issueIndex": issue_index,
                "issue_index": issue_index,
                "rowIndex": row_index,
                "row_index": row_index,
                "section_index": issue.get("section_index"),
                "hunk": issue.get("hunk"),
                "section_offset": issue.get("section_offset"),
                "summary": summary,
                "matchText": issue.get("match_text"),
                "match_text": issue.get("match_text"),
                "stableKey": issue.get("stable_key"),
                "stable_key": issue.get("stable_key"),
            }
        )
    return entries


def issues_by_row_index(report: dict[str, object]) -> dict[int, list[dict[str, object]]]:
    grouped: dict[int, list[dict[str, object]]] = {}
    for issue in _dict_list(report.get("issues")):
        row_index = issue.get("row_index")
        if isinstance(row_index, int):
            grouped.setdefault(row_index, []).append(issue)
    return grouped


def _write_reproduction_report(target_dir: Path, report: dict[str, object]) -> dict[str, object]:
    path = reproduction_report_path(target_dir)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _write_text_if_changed(path: Path, text: str) -> tuple[int, bool]:
    data = text.encode("utf-8")
    try:
        if path.read_bytes() == data:
            return len(data), False
    except OSError:
        pass
    path.write_bytes(data)
    return len(data), True


def facts_v2_direct_source_compare_enabled() -> bool:
    return os.environ.get(FACTS_V2_DIRECT_SOURCE_COMPARE_ENV) in {"1", "true", "True", "yes", "YES"}


def _write_source_artifact(path: Path, text: str, profile_timings: dict[str, object]) -> int:
    started_at = time.perf_counter()
    source_size, source_written = _write_text_if_changed(path, text)
    profile_timings["source_file_rewritten"] = 1.0 if source_written else 0.0
    _record_profile_timing(profile_timings, "write_source_seconds", started_at)
    return source_size


def _issue(
    kind: str,
    message: str,
    row_ref: tuple[int, Mapping[str, object]] | None,
    *,
    diff_range: dict[str, object] | None = None,
    layout_range: dict[str, object] | None = None,
    section_index: int | None = None,
    section_offset: int | None = None,
    hunk: int | None = None,
) -> dict[str, object]:
    row_index: int | None = None
    row: Mapping[str, object] | None = None
    if row_ref is not None:
        row_index, row = row_ref
    if row is not None and section_index is None:
        section_index = _row_int(row, "section_index")
    if hunk is None:
        hunk = section_index
    payload: dict[str, object] = {
        "kind": kind,
        "message": message,
        "summary": message,
        "row_index": row_index,
        "addr": _row_int(row, "addr") if row is not None else None,
        "section_index": section_index,
        "section_offset": section_offset,
        "hunk": hunk,
        "stable_key": _row_str(row, "stable_key") if row is not None else None,
        "match_text": _row_match_text(row) if row is not None else None,
    }
    if diff_range is not None:
        payload["diff_range"] = diff_range
    if layout_range is not None:
        payload["layout_range"] = layout_range
        payload["layout_kind"] = layout_range.get("kind")
    return payload


def _row_match_text(row: Mapping[str, object]) -> str:
    label = _row_str(row, "label")
    if label:
        return label
    opcode = _row_str(row, "opcode_or_directive")
    if opcode:
        operand_text = _row_str(row, "operand_text") or ""
        return " ".join(part for part in (opcode, operand_text) if part).strip()
    return str(row.get("text") or "").strip()


def _row_int(row: Mapping[str, object], key: str) -> int | None:
    value = row.get(key)
    return value if isinstance(value, int) else None


def _row_str(row: Mapping[str, object], key: str) -> str | None:
    value = row.get(key)
    return value if isinstance(value, str) else None


def _diff_range(start: int, end: int, original: bytes, rebuilt: bytes) -> dict[str, object]:
    return {
        "start": start,
        "end": end,
        "length": end - start,
        "original_hex": original[start:min(end, len(original))].hex(),
        "rebuilt_hex": rebuilt[start:min(end, len(rebuilt))].hex(),
    }


def _diff_summary(
    diff_range: dict[str, object],
    *,
    layout_range: dict[str, object] | None = None,
    section_offset: int | None = None,
) -> str:
    start = _required_int(diff_range.get("start"))
    length = _required_int(diff_range.get("length"))
    location = f"file offset 0x{start:X}"
    if layout_range is not None:
        layout_kind = str(layout_range.get("kind") or "file").replace("_", " ")
        if layout_kind == "section payload" and section_offset is not None:
            section_index = layout_range.get("section_index")
            location = f"section {section_index} offset 0x{section_offset:X} (file 0x{start:X})"
        else:
            location = f"{layout_kind} at file offset 0x{start:X}"
    if length == 1:
        return f"Diff at {location}"
    return f"Diff at {location}, {length} bytes"


def _platform_file_lib_path(project_root: Path) -> Path:
    return project_root / "src" / "build" / "platform_file_lib.dll"


def _include_dir_for_backend(backend: str, project_root: Path) -> Path | None:
    if backend in {"amiga-hunk", "amiga-raw"}:
        return project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    if backend == "atari-st":
        return project_root / "ext" / "atarist_includes" / "devpac_3_10" / "include"
    return None


def _file_stamp(path: Path) -> str:
    try:
        stat = path.stat()
    except OSError:
        return "missing"
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_renderer_tool_stamps(project_root: Path) -> dict[str, str]:
    build_dir = project_root / "src" / "build"
    return {
        "c_backend.py": _file_stamp(Path(__file__).with_name("c_backend.py")),
        "platform_file_lib.dll": _file_stamp(build_dir / "platform_file_lib.dll"),
        "platform_disk_lib.dll": _file_stamp(build_dir / "platform_disk_lib.dll"),
    }


def _base_reproduction_report(
    target_name: str,
    *,
    started_at: float,
    input_stamp: dict[str, object],
    assembler: str,
    backend: str,
    source_path: Path,
    rebuilt_path: Path,
) -> dict[str, object]:
    return {
        "target": target_name,
        "status": "not_ready",
        "exact": False,
        "stale": False,
        "input_stamp": input_stamp,
        "started_at": started_at,
        "finished_at": None,
        "assembler": assembler,
        "assembler_cpu": input_stamp.get("assembler_cpu"),
        "backend": backend,
        "analysis_backend": input_stamp.get("analysis_backend"),
        "source_path": str(source_path),
        "rebuilt_path": str(rebuilt_path),
        "original_size": input_stamp.get("original_size"),
        "rebuilt_size": None,
        "original_sha256": input_stamp.get("original_sha256"),
        "rebuilt_sha256": None,
        "direct_source_exact": None,
        "direct_source_assembler": None,
        "direct_source_diff_range_count": None,
        "direct_source_first_diff": None,
        "first_diff": None,
        "diff_ranges": [],
        "row_mappings": [],
        "issues": [],
        "assembler_diagnostics": [],
        "assembler_stdout": "",
        "assembler_stderr": "",
        "file_shape_adjustments": [],
        "tool_error": None,
    }


def _emit_progress(
    progress_callback: Callable[[dict[str, object]], None] | None,
    *,
    target_name: str,
    phase: str,
    started_at: float,
    **payload: object,
) -> None:
    if progress_callback is None:
        return
    event: dict[str, object] = {
        "target": target_name,
        "phase": phase,
        "updated_at": time.time(),
        "elapsed_seconds": round(time.perf_counter() - started_at, 4),
    }
    for key, value in payload.items():
        if value is not None:
            event[key] = value
    progress_callback(event)


def _record_profile_timing(
    timings: dict[str, object],
    key: str,
    started_at: float,
) -> None:
    timings[key] = round(time.perf_counter() - started_at, 4)


def _merge_assembler_profile(timings: dict[str, object], profile: dict[str, object]) -> None:
    for key, value in profile.items():
        if isinstance(value, bool):
            timings[f"assembler_{key}"] = 1.0 if value else 0.0
        elif key.endswith("_bytes") and isinstance(value, int):
            timings[f"assembler_{key}"] = value
        elif isinstance(value, (int, float)):
            timings[f"assembler_{key}"] = round(float(value), 6)


def _merge_direct_rebuild_profile(timings: dict[str, object], profile: dict[str, object]) -> None:
    for key, value in profile.items():
        if key.startswith("facts_v2_"):
            output_key = key
        elif key.startswith("direct_"):
            output_key = f"facts_v2_{key}"
        else:
            output_key = f"facts_v2_direct_{key}"
        if isinstance(value, bool):
            timings[output_key] = 1.0 if value else 0.0
        elif key.endswith("_bytes") and isinstance(value, int):
            timings[output_key] = value
        elif isinstance(value, (int, float)):
            timings[output_key] = round(float(value), 6)
        elif isinstance(value, str) and value:
            timings[output_key] = value


def _record_direct_source_comparison(
    timings: dict[str, object],
    direct_bytes: bytes,
    source_bytes: bytes,
    *,
    compare_profile: dict[str, object] | None = None,
) -> None:
    timings["facts_v2_direct_source_compare"] = 1.0
    timings["facts_v2_direct_rebuilt_bytes"] = len(direct_bytes)
    timings["facts_v2_source_assembled_bytes"] = len(source_bytes)
    timings["facts_v2_direct_rebuilt_sha256"] = _sha256_bytes(direct_bytes)
    timings["facts_v2_source_assembled_sha256"] = _sha256_bytes(source_bytes)
    timings["facts_v2_direct_source_match"] = 1.0 if direct_bytes == source_bytes else 0.0
    timings["facts_v2_direct_source_mismatch"] = 0.0 if direct_bytes == source_bytes else 1.0
    if compare_profile is None:
        return
    exactness_id = _direct_profile_int(compare_profile, "direct_compare_exactness_id") or 0
    timings["facts_v2_source_full_file_exact"] = 1.0 if exactness_id == 1 else 0.0
    timings["facts_v2_source_content_exact"] = 1.0 if exactness_id in {1, 2} else 0.0
    timings["facts_v2_source_payload_exact"] = (
        1.0 if compare_profile.get("direct_compare_payload_exact") is True else 0.0
    )
    if "direct_compare_relocation_semantics_exact" in compare_profile:
        timings["facts_v2_source_relocation_semantics_exact"] = (
            1.0 if compare_profile.get("direct_compare_relocation_semantics_exact") is True else 0.0
        )
    if "direct_compare_status_id" in compare_profile:
        timings["facts_v2_source_compare_status_id"] = _direct_profile_int(
            compare_profile, "direct_compare_status_id"
        ) or 0
    if "direct_compare_issue_group_flags" in compare_profile:
        timings["facts_v2_source_compare_issue_group_flags"] = _direct_profile_int(
            compare_profile, "direct_compare_issue_group_flags"
        ) or 0


def _direct_source_report_fields(original: bytes, source_bytes: bytes, *, assembler: str) -> dict[str, object]:
    return _direct_source_report_fields_from_ranges(
        original,
        source_bytes,
        assembler=assembler,
        diff_ranges=grouped_diff_ranges(original, source_bytes),
    )


def _direct_source_report_fields_from_ranges(
    original: bytes,
    source_bytes: bytes,
    *,
    assembler: str,
    diff_ranges: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "direct_source_exact": not diff_ranges,
        "direct_source_assembler": assembler,
        "direct_source_diff_range_count": len(diff_ranges),
        "direct_source_first_diff": _first_diff_from_ranges(original, source_bytes, diff_ranges),
    }


def _profile_timing_total(profile: dict[str, object] | None) -> float:
    if not isinstance(profile, dict):
        return 0.0
    timing = profile.get("timing")
    if not isinstance(timing, dict):
        return 0.0
    value = timing.get("total_seconds")
    return round(float(value), 6) if isinstance(value, (int, float)) else 0.0


def _flat_profile_total(profile: dict[str, object] | None) -> float:
    if not isinstance(profile, dict):
        return 0.0
    value = profile.get("total_seconds")
    return round(float(value), 6) if isinstance(value, (int, float)) else 0.0


def _facts_v2_profile_source_bytes(profile: dict[str, object] | None) -> int:
    if not isinstance(profile, dict):
        return 0
    facts_v2 = profile.get("facts_v2")
    if not isinstance(facts_v2, dict):
        return 0
    value = facts_v2.get("asm_source_bytes")
    return int(value) if isinstance(value, int) else 0


def _accepted_direct_rebuild_refusal_kind(
    backend: str,
    *,
    source_profile: dict[str, object] | None,
    direct_profile: dict[str, object],
) -> str | None:
    if backend != "amiga-hunk":
        return None
    if direct_profile.get("direct_rebuild_refusal_reason") != "lossy_numeric_hunk_relocations":
        return None
    lossy_counters = (
        "asm_source_lossy_numeric_hunk_relocations",
        "unassemblable_hunk_data_relocations",
        "unassemblable_hunk_base_register_relocations",
        "asm_source_unassemblable_hunk_data_relocation_refusals",
        "asm_source_unassemblable_hunk_base_register_relocation_refusals",
    )
    if any(_facts_v2_profile_counter(source_profile, key) > 0 for key in lossy_counters):
        return "lossy_hunk_reloc32"
    return None


def _facts_v2_profile_counter(profile: dict[str, object] | None, key: str) -> int:
    if not isinstance(profile, dict):
        return 0
    facts_v2 = profile.get("facts_v2")
    if not isinstance(facts_v2, dict):
        return 0
    value = facts_v2.get(key)
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else 0


def _profile_payload(timings: dict[str, object], started_at: float) -> dict[str, object]:
    payload: dict[str, object] = dict(timings)
    payload["total_seconds"] = round(time.perf_counter() - started_at, 4)
    return payload


def _default_reproduction_options() -> dict[str, object]:
    return {
        "mode": "exact",
        "assembler": "our",
        "cpu": "any",
        "backend": "auto",
        "include_dirs": "auto",
        "oracle_modes": [],
        "container_policy": "preserve_original",
        "relocation_policy": "preserve_original_encoding",
        "comparison": "full_file",
        "requested_exactness": "full_file",
        "requested_exactness_id": 1,
        "file_shape": {
            "relocation_order": "match_original",
            "relocation_record": "auto",
            "section_aux_order": "assembler-default",
        },
        "raw_output": None,
    }


def _reproduction_option_payloads(target_dir: Path) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for file_name in (
        TARGET_METADATA_FILE_NAME,
        TARGET_SEEDED_METADATA_FILE_NAME,
        TARGET_CORRECTIONS_FILE_NAME,
    ):
        metadata_payload = _read_json_object(target_dir / file_name)
        reproduction_payload = metadata_payload.get("reproduction")
        if isinstance(reproduction_payload, dict):
            payloads.append(cast(dict[str, object], reproduction_payload))
    edits_payload = _read_json_list(target_dir / TARGET_UI_EDITS_FILE_NAME)
    for edit in edits_payload:
        if not isinstance(edit, dict) or edit.get("kind") not in {"reproduction", "reproduction_options"}:
            continue
        options_payload = edit.get("options")
        if not isinstance(options_payload, dict):
            options_payload = edit.get("reproduction")
        if isinstance(options_payload, dict):
            payloads.append(cast(dict[str, object], options_payload))
    return payloads


def _merge_reproduction_options(options: dict[str, object], payload: dict[str, object]) -> None:
    mode = _normalized_reproduction_value(payload.get("mode"))
    if mode in REPRODUCTION_MODES:
        options["mode"] = mode
    assembler = payload.get("assembler")
    if isinstance(assembler, str):
        options["assembler"] = assembler
    cpu = payload.get("cpu")
    if cpu in REPRODUCTION_CPUS:
        options["cpu"] = cpu
    backend = payload.get("backend")
    if backend in REPRODUCTION_BACKENDS:
        options["backend"] = backend
    include_dirs = payload.get("include_dirs")
    if include_dirs == "auto":
        options["include_dirs"] = "auto"
    elif isinstance(include_dirs, list) and all(isinstance(item, str) for item in include_dirs):
        options["include_dirs"] = list(include_dirs)
    oracle_modes = payload.get("oracle_modes")
    if isinstance(oracle_modes, list):
        options["oracle_modes"] = [
            item for item in oracle_modes if isinstance(item, str) and item in REPRODUCTION_ORACLE_MODES
        ]
    container_policy = _normalized_reproduction_value(payload.get("container_policy"))
    if container_policy in REPRODUCTION_CONTAINER_POLICIES:
        options["container_policy"] = container_policy
    relocation_policy = _normalized_reproduction_value(payload.get("relocation_policy"))
    if relocation_policy in REPRODUCTION_RELOCATION_POLICIES:
        options["relocation_policy"] = relocation_policy
    comparison = _normalized_reproduction_value(payload.get("comparison"))
    if comparison in REPRODUCTION_COMPARISONS:
        options["comparison"] = comparison
    requested_exactness = _normalized_reproduction_value(payload.get("requested_exactness"))
    if requested_exactness in REPRODUCTION_REQUESTED_EXACTNESS:
        options["requested_exactness"] = requested_exactness
        options["requested_exactness_id"] = REPRODUCTION_REQUESTED_EXACTNESS_IDS[requested_exactness]
    if "raw_output" in payload:
        raw_output = payload["raw_output"]
        if raw_output is None or isinstance(raw_output, (str, dict)):
            options["raw_output"] = raw_output
    file_shape_payload = payload.get("file_shape")
    if isinstance(file_shape_payload, dict):
        file_shape = cast(dict[str, object], options["file_shape"])
        relocation_order = file_shape_payload.get("relocation_order")
        if relocation_order in {"assembler-default", "match_original"}:
            file_shape["relocation_order"] = relocation_order
            if relocation_order == "assembler-default" and "relocation_policy" not in payload:
                options["relocation_policy"] = "assembler_default"
            elif relocation_order == "match_original" and "relocation_policy" not in payload:
                options["relocation_policy"] = "preserve_original_encoding"
        relocation_record = file_shape_payload.get("relocation_record")
        if relocation_record in {"auto", "long", "short"}:
            file_shape["relocation_record"] = relocation_record
        section_aux_order = file_shape_payload.get("section_aux_order")
        if section_aux_order in {"assembler-default", "match_original"}:
            file_shape["section_aux_order"] = section_aux_order


def reproduction_policy_for_options(options: dict[str, object]) -> dict[str, object]:
    mode = _normalized_reproduction_value(options.get("mode"))
    if mode not in REPRODUCTION_MODES:
        mode = "exact"
    container_policy = _normalized_reproduction_value(options.get("container_policy"))
    if container_policy not in REPRODUCTION_CONTAINER_POLICIES:
        container_policy = "preserve_original"
    relocation_policy = _normalized_reproduction_value(options.get("relocation_policy"))
    if relocation_policy not in REPRODUCTION_RELOCATION_POLICIES:
        relocation_policy = "preserve_original_encoding"
    comparison = _normalized_reproduction_value(options.get("comparison"))
    if comparison not in REPRODUCTION_COMPARISONS:
        comparison = "full_file"
    requested_exactness = _normalized_reproduction_value(options.get("requested_exactness"))
    if requested_exactness not in REPRODUCTION_REQUESTED_EXACTNESS:
        requested_exactness = "full_file"
    requested_exactness_id = REPRODUCTION_REQUESTED_EXACTNESS_IDS[requested_exactness]
    if mode == "template_preserved":
        container_policy = "preserve_original"
        relocation_policy = "preserve_original_encoding"
        comparison = "full_file"
    elif mode == "canonical":
        container_policy = "assembler_default"
        relocation_policy = "assembler_default"
        comparison = "full_file"
    elif mode == "content":
        comparison = "content"
    elif mode == "semantic":
        comparison = "semantic"
    return {
        "mode": mode,
        "container_policy": container_policy,
        "relocation_policy": relocation_policy,
        "comparison": comparison,
        "requested_exactness": requested_exactness,
        "requested_exactness_id": requested_exactness_id,
    }


def _normalized_reproduction_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().lower().replace("-", "_")


def _effective_reproduction_backend(default_backend: str, options: dict[str, object]) -> str:
    backend = options.get("backend")
    return backend if isinstance(backend, str) and backend != "auto" else default_backend


def _effective_reproduction_assembler(default_assembler: str, options: dict[str, object]) -> str:
    assembler = options.get("assembler")
    return assembler if isinstance(assembler, str) and assembler else default_assembler


def _effective_reproduction_cpu(options: dict[str, object]) -> str:
    cpu = options.get("cpu")
    return cpu if isinstance(cpu, str) and cpu in REPRODUCTION_CPUS else "any"


def _best_effort_effective_metadata_hash(target_dir: Path) -> str | None:
    try:
        return effective_metadata_hash(target_dir)
    except Exception:
        return None


def _best_effort_target_dir(target_name: str, *, project_root: Path) -> Path | None:
    try:
        resolved = resolve_project_dir(target_name, project_root=project_root)
        if isinstance(resolved, Path):
            return resolved
        return None
    except Exception:
        candidate = project_root / "targets" / target_name
        return candidate if candidate.exists() else None


def _read_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return cast(dict[str, object], payload) if isinstance(payload, dict) else {}


def _read_json_list(path: Path) -> list[object]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast(dict[str, object], item) for item in value if isinstance(item, dict)]


def _required_int(value: object) -> int:
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected int value, got {type(value).__name__}")


def _optional_int(value: object, fallback: int) -> int:
    return value if isinstance(value, int) else fallback


def _atari_st_file_layout(data: bytes) -> list[dict[str, object]]:
    layout: list[dict[str, object]] = []
    if len(data) < _ATARI_PRG_HEADER_SIZE or _u16be(data, 0) != _ATARI_PRG_MAGIC:
        _append_layout_range(layout, "unknown", 0, len(data), data_len=len(data), label="unknown Atari file")
        return layout
    _append_layout_range(layout, "header", 0, _ATARI_PRG_HEADER_SIZE, data_len=len(data), label="Atari PRG header")
    text_size = _u32be(data, 2)
    data_size = _u32be(data, 6)
    symbol_size = _u32be(data, 14)
    offset = _ATARI_PRG_HEADER_SIZE
    _append_layout_range(
        layout,
        "section_payload",
        offset,
        offset + text_size,
        data_len=len(data),
        section_index=0,
        hunk=0,
        section_offset_start=0,
        label="text payload",
    )
    offset += text_size
    _append_layout_range(
        layout,
        "section_payload",
        offset,
        offset + data_size,
        data_len=len(data),
        section_index=1,
        hunk=1,
        section_offset_start=0,
        label="data payload",
    )
    offset += data_size
    _append_layout_range(layout, "symbol_table", offset, offset + symbol_size, data_len=len(data), label="symbol table")
    offset += symbol_size
    if offset < len(data):
        _append_layout_range(layout, "relocation", offset, len(data), data_len=len(data), label="relocation table")
    return layout


def _amiga_hunk_file_layout(data: bytes) -> list[dict[str, object]]:
    layout: list[dict[str, object]] = []
    if len(data) < 4 or _u32be(data, 0) != _HUNK_HEADER:
        _append_layout_range(layout, "unknown", 0, len(data), data_len=len(data), label="unknown hunk file")
        return layout
    try:
        _append_amiga_hunk_executable_layout(layout, data)
    except ValueError:
        last_end = max((_required_int(entry.get("file_end") or 0) for entry in layout), default=0)
        _append_layout_range(layout, "unknown", last_end, len(data), data_len=len(data), label="unparsed hunk data")
    return layout


def _append_amiga_hunk_executable_layout(layout: list[dict[str, object]], data: bytes) -> None:
    pos = 4
    while True:
        longs = _read_u32be(data, pos)
        pos += 4
        pos = _skip_bytes_checked(data, pos, longs * 4)
        if longs == 0:
            break
    table_size = _read_u32be(data, pos)
    pos += 4
    first_hunk = _read_u32be(data, pos)
    pos += 4
    last_hunk = _read_u32be(data, pos)
    pos += 4
    count = (last_hunk - first_hunk + 1) if last_hunk >= first_hunk else table_size
    header_mem_attrs: list[int] = []
    for _index in range(count):
        size_word = _read_u32be(data, pos)
        pos += 4
        mem_attrs = 0
        if (size_word >> _HUNK_MEM_SHIFT) == 3:
            mem_attrs = _read_u32be(data, pos)
            pos += 4
        header_mem_attrs.append(mem_attrs)
    _append_layout_range(layout, "header", 0, pos, data_len=len(data), label="Amiga hunk header")
    for section_index in range(count):
        section_start = pos
        raw_type = _read_u32be(data, pos)
        pos += 4
        hunk_id = raw_type & _HUNK_TYPE_ID_MASK
        if hunk_id not in _HUNK_SECTION_TYPES:
            _append_layout_range(
                layout,
                "unknown",
                section_start,
                len(data),
                data_len=len(data),
                section_index=section_index,
                hunk=section_index,
                label="unexpected hunk section",
            )
            return
        mem_type = raw_type >> _HUNK_MEM_SHIFT
        if mem_type == 3 and header_mem_attrs[section_index] == 0:
            pos = _skip_bytes_checked(data, pos, 4)
        size_longs = _read_u32be(data, pos)
        pos += 4
        payload_start = pos
        if hunk_id in {_HUNK_CODE, _HUNK_DATA}:
            payload_end = _skip_bytes_checked(data, payload_start, size_longs * 4)
            _append_layout_range(
                layout,
                "section_header",
                section_start,
                payload_start,
                data_len=len(data),
                section_index=section_index,
                hunk=section_index,
                label="hunk section header",
            )
            _append_layout_range(
                layout,
                "section_payload",
                payload_start,
                payload_end,
                data_len=len(data),
                section_index=section_index,
                hunk=section_index,
                section_offset_start=0,
                label="hunk section payload",
            )
            pos = payload_end
        else:
            _append_layout_range(
                layout,
                "section_header",
                section_start,
                pos,
                data_len=len(data),
                section_index=section_index,
                hunk=section_index,
                label="hunk BSS header",
            )
        pos = _append_amiga_hunk_aux_layout(layout, data, pos, section_index)


def _append_amiga_hunk_aux_layout(
    layout: list[dict[str, object]],
    data: bytes,
    pos: int,
    section_index: int,
) -> int:
    while pos < len(data):
        record_start = pos
        raw = _read_u32be(data, pos)
        pos += 4
        hunk_id = raw & _HUNK_TYPE_ID_MASK
        if hunk_id == _HUNK_END:
            _append_layout_range(
                layout,
                "section_end",
                record_start,
                pos,
                data_len=len(data),
                section_index=section_index,
                hunk=section_index,
                label="hunk end",
            )
            return pos
        if hunk_id == _HUNK_SYMBOL:
            pos = _skip_hunk_symbol_block(data, pos)
            kind = "symbol"
        elif hunk_id == _HUNK_DEBUG:
            size_longs = _read_u32be(data, pos)
            pos = _skip_bytes_checked(data, pos + 4, size_longs * 4)
            kind = "debug"
        elif hunk_id in _HUNK_RELOCATION_LONG_TYPES:
            pos = _skip_hunk_relocation_block(data, pos, short_counts=False)
            kind = "relocation"
        elif hunk_id == _HUNK_RELOC32SHORT:
            pos = _skip_hunk_relocation_block(data, pos, short_counts=True)
            kind = "relocation"
        elif hunk_id == _HUNK_EXT:
            pos = _skip_hunk_ext_block(data, pos)
            kind = "external"
        else:
            size_longs = _read_u32be(data, pos)
            pos = _skip_bytes_checked(data, pos + 4, size_longs * 4)
            kind = "unknown"
        _append_layout_range(
            layout,
            kind,
            record_start,
            pos,
            data_len=len(data),
            section_index=section_index,
            hunk=section_index,
            label=f"hunk {kind}",
        )
    return pos


def _split_diff_range_by_layout(
    diff_range: dict[str, object],
    file_layout: list[dict[str, object]],
) -> list[tuple[dict[str, object], dict[str, object] | None]]:
    start = _required_int(diff_range.get("start"))
    end = _required_int(diff_range.get("end"))
    if end <= start:
        return [(diff_range, _layout_range_for_file_offset(file_layout, start))]
    chunks: list[tuple[dict[str, object], dict[str, object] | None]] = []
    cursor = start
    while cursor < end:
        layout_range = _layout_range_for_file_offset(file_layout, cursor)
        chunk_end = end
        if layout_range is not None:
            chunk_end = min(end, _required_int(layout_range.get("file_end")))
        else:
            next_start = min(
                (
                    _required_int(item.get("file_start"))
                    for item in file_layout
                    if _required_int(item.get("file_start")) > cursor
                ),
                default=end,
            )
            chunk_end = min(end, next_start)
        if chunk_end <= cursor:
            chunk_end = cursor + 1
        issue_range = dict(diff_range)
        issue_range["start"] = cursor
        issue_range["end"] = chunk_end
        issue_range["length"] = chunk_end - cursor
        issue_range.pop("original_hex", None)
        issue_range.pop("rebuilt_hex", None)
        chunks.append((issue_range, layout_range))
        cursor = chunk_end
    return chunks


def _layout_range_for_file_offset(
    file_layout: list[dict[str, object]],
    offset: int,
) -> dict[str, object] | None:
    for item in file_layout:
        if _required_int(item.get("file_start")) <= offset < _required_int(item.get("file_end")):
            return item
    return None


def _layout_int(layout_range: dict[str, object] | None, key: str) -> int | None:
    if layout_range is None:
        return None
    value = layout_range.get(key)
    return value if isinstance(value, int) else None


def _section_payload_ranges(file_layout: list[dict[str, object]]) -> dict[int, tuple[int, int]]:
    ranges: dict[int, tuple[int, int]] = {}
    for item in file_layout:
        if item.get("kind") != "section_payload":
            continue
        section_index = _layout_int(item, "section_index")
        if section_index is None:
            continue
        ranges[section_index] = (
            _required_int(item.get("file_start")),
            _required_int(item.get("file_end")),
        )
    return ranges


def _comparison_failure_kinds(
    *,
    payload_exact: bool,
    relocation_semantics: bool | None,
    relocation_encoding: bool | None,
    diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> list[str]:
    kinds: list[str] = []
    if not payload_exact:
        kinds.append("payload_mismatch")
    if relocation_semantics is False:
        kinds.append("relocation_semantic_mismatch")
    elif relocation_encoding is False:
        kinds.append("relocation_encoding_mismatch")
    for layout_kind in _diff_layout_kinds(diff_ranges, file_layout):
        shape_kind = _layout_kind_failure_kind(layout_kind)
        if shape_kind not in kinds:
            kinds.append(shape_kind)
    return kinds


def _diff_layout_kinds(
    diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> list[str]:
    kinds: list[str] = []
    for diff_range in diff_ranges:
        start = diff_range.get("start")
        if not isinstance(start, int):
            continue
        layout_range = _layout_range_for_file_offset(file_layout, start)
        kind = layout_range.get("kind") if layout_range is not None else None
        if isinstance(kind, str) and kind not in kinds:
            kinds.append(kind)
    return kinds


def _layout_kind_failure_kind(layout_kind: str) -> str:
    if layout_kind == "section_payload":
        return "payload_mismatch"
    if layout_kind == "relocation":
        return "relocation_encoding_mismatch"
    if layout_kind in {"header", "section_header", "section_end"}:
        return "header_shape_mismatch"
    if layout_kind in {"symbol", "external", "debug", "symbol_table"}:
        return f"{layout_kind}_shape_mismatch"
    return f"{layout_kind}_mismatch"


def _append_layout_range(
    layout: list[dict[str, object]],
    kind: str,
    file_start: int,
    file_end: int,
    *,
    data_len: int,
    section_index: int | None = None,
    hunk: int | None = None,
    section_offset_start: int | None = None,
    label: str | None = None,
) -> None:
    start = max(0, min(file_start, data_len))
    end = max(start, min(file_end, data_len))
    if end <= start:
        return
    entry: dict[str, object] = {
        "kind": kind,
        "file_start": start,
        "file_end": end,
        "length": end - start,
    }
    if section_index is not None:
        entry["section_index"] = section_index
    if hunk is not None:
        entry["hunk"] = hunk
    if section_offset_start is not None:
        entry["section_offset_start"] = section_offset_start
    if label:
        entry["label"] = label
    layout.append(entry)


def _amiga_hunk_relocation_groups(data: bytes) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for block in _amiga_hunk_relocation_blocks(data):
        groups.extend(cast(list[dict[str, object]], block["groups"]))
    return groups


def _amiga_hunk_relocation_blocks(data: bytes) -> list[dict[str, object]]:
    blocks: list[dict[str, object]] = []
    if len(data) < 4 or _u32be(data, 0) != _HUNK_HEADER:
        return blocks
    pos = 4
    while True:
        longs = _read_u32be(data, pos)
        pos += 4
        pos = _skip_bytes_checked(data, pos, longs * 4)
        if longs == 0:
            break
    table_size = _read_u32be(data, pos)
    pos += 4
    first_hunk = _read_u32be(data, pos)
    pos += 4
    last_hunk = _read_u32be(data, pos)
    pos += 4
    section_count = (last_hunk - first_hunk + 1) if last_hunk >= first_hunk else table_size
    header_mem_attrs: list[int] = []
    for _index in range(section_count):
        size_word = _read_u32be(data, pos)
        pos += 4
        mem_attrs = 0
        if (size_word >> _HUNK_MEM_SHIFT) == 3:
            mem_attrs = _read_u32be(data, pos)
            pos += 4
        header_mem_attrs.append(mem_attrs)
    for section_index in range(section_count):
        raw_type = _read_u32be(data, pos)
        pos += 4
        hunk_id = raw_type & _HUNK_TYPE_ID_MASK
        if hunk_id not in _HUNK_SECTION_TYPES:
            return blocks
        mem_type = raw_type >> _HUNK_MEM_SHIFT
        if mem_type == 3 and header_mem_attrs[section_index] == 0:
            pos = _skip_bytes_checked(data, pos, 4)
        size_longs = _read_u32be(data, pos)
        pos += 4
        if hunk_id in {_HUNK_CODE, _HUNK_DATA}:
            pos = _skip_bytes_checked(data, pos, size_longs * 4)
        while pos < len(data):
            record_file_start = pos
            raw = _read_u32be(data, pos)
            pos += 4
            record_id = raw & _HUNK_TYPE_ID_MASK
            if record_id == _HUNK_END:
                break
            if record_id in _HUNK_RELOCATION_LONG_TYPES:
                pos, block_groups = _read_hunk_relocation_block(
                    data,
                    pos,
                    section_index=section_index,
                    record_id=record_id,
                    short_counts=False,
                )
                blocks.append(
                    _hunk_relocation_block(
                        section_index,
                        record_id,
                        False,
                        record_file_start,
                        pos,
                        block_groups,
                    )
                )
            elif record_id == _HUNK_RELOC32SHORT:
                pos, block_groups = _read_hunk_relocation_block(
                    data,
                    pos,
                    section_index=section_index,
                    record_id=record_id,
                    short_counts=True,
                )
                blocks.append(
                    _hunk_relocation_block(
                        section_index,
                        record_id,
                        True,
                        record_file_start,
                        pos,
                        block_groups,
                    )
                )
            elif record_id == _HUNK_SYMBOL:
                pos = _skip_hunk_symbol_block(data, pos)
            elif record_id == _HUNK_DEBUG:
                size_longs = _read_u32be(data, pos)
                pos = _skip_bytes_checked(data, pos + 4, size_longs * 4)
            elif record_id == _HUNK_EXT:
                pos = _skip_hunk_ext_block(data, pos)
            else:
                size_longs = _read_u32be(data, pos)
                pos = _skip_bytes_checked(data, pos + 4, size_longs * 4)
    return blocks


def _hunk_relocation_block(
    section_index: int,
    record_id: int,
    short_counts: bool,
    file_start: int,
    file_end: int,
    groups: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "section_index": section_index,
        "record_id": record_id,
        "short_counts": short_counts,
        "file_start": file_start,
        "file_end": file_end,
        "groups": groups,
    }


def _read_hunk_relocation_block(
    data: bytes,
    pos: int,
    *,
    section_index: int,
    record_id: int,
    short_counts: bool,
) -> tuple[int, list[dict[str, object]]]:
    groups: list[dict[str, object]] = []
    while True:
        offsets: list[int] = []
        group_file_start = pos
        if short_counts:
            count = _read_u16be(data, pos)
            pos += 2
            if count == 0:
                if pos & 3:
                    pos = _skip_bytes_checked(data, pos, 2)
                return pos, groups
            target_section = _read_u16be(data, pos)
            pos += 2
            offsets_file_start = pos
            for _index in range(count):
                offsets.append(_read_u16be(data, pos))
                pos += 2
        else:
            count = _read_u32be(data, pos)
            pos += 4
            if count == 0:
                return pos, groups
            target_section = _read_u32be(data, pos)
            pos += 4
            offsets_file_start = pos
            for _index in range(count):
                offsets.append(_read_u32be(data, pos))
                pos += 4
        groups.append(
            {
                "section_index": section_index,
                "record_id": record_id,
                "target_section": target_section,
                "short_counts": short_counts,
                "group_file_start": group_file_start,
                "group_file_end": pos,
                "offsets_file_start": offsets_file_start,
                "offsets": offsets,
            }
        )


def _first_diff_layout_kind(
    diff_ranges: list[dict[str, object]],
    file_layout: list[dict[str, object]],
) -> str | None:
    if not diff_ranges:
        return None
    first_start = diff_ranges[0].get("start")
    if not isinstance(first_start, int):
        return None
    layout_range = _layout_range_for_file_offset(file_layout, first_start)
    if layout_range is None:
        return None
    kind = layout_range.get("kind")
    return kind if isinstance(kind, str) else None


def _atari_st_header_fields(data: bytes) -> dict[str, int] | None:
    if len(data) < _ATARI_PRG_HEADER_SIZE or _u16be(data, 0) != _ATARI_PRG_MAGIC:
        return None
    return {
        "magic": _u16be(data, 0),
        "text_size": _u32be(data, 2),
        "data_size": _u32be(data, 6),
        "bss_size": _u32be(data, 10),
        "symbol_size": _u32be(data, 14),
        "reserved": _u32be(data, 18),
        "flags": _u32be(data, 22),
        "relocation_flag": _u16be(data, 26),
    }


def _atari_st_relocation_offset(data: bytes) -> int:
    header = _atari_st_header_fields(data)
    if header is None:
        return len(data)
    return _ATARI_PRG_HEADER_SIZE + header["text_size"] + header["data_size"] + header["symbol_size"]


def _skip_hunk_symbol_block(data: bytes, pos: int) -> int:
    while True:
        name_longs = _read_u32be(data, pos)
        pos += 4
        if name_longs == 0:
            return pos
        pos = _skip_bytes_checked(data, pos, name_longs * 4 + 4)


def _skip_hunk_relocation_block(data: bytes, pos: int, *, short_counts: bool) -> int:
    if short_counts:
        while True:
            count = _read_u16be(data, pos)
            pos += 2
            if count == 0:
                if pos & 3:
                    pos = _skip_bytes_checked(data, pos, 2)
                return pos
            pos = _skip_bytes_checked(data, pos, 2 + count * 2)
    while True:
        count = _read_u32be(data, pos)
        pos += 4
        if count == 0:
            return pos
        pos = _skip_bytes_checked(data, pos, 4 + count * 4)


def _skip_hunk_ext_block(data: bytes, pos: int) -> int:
    while True:
        tag = _read_u32be(data, pos)
        pos += 4
        if tag == 0:
            return pos
        ext_type = tag >> 24
        name_longs = tag & 0xFFFFFF
        pos = _skip_bytes_checked(data, pos, name_longs * 4)
        if ext_type in _HUNK_EXT_DEFINITION_TYPES:
            pos = _skip_bytes_checked(data, pos, 4)
        elif ext_type in _HUNK_EXT_REFERENCE_TYPES or ext_type in _HUNK_EXT_COMMON_REFERENCE_TYPES:
            if ext_type in _HUNK_EXT_COMMON_REFERENCE_TYPES:
                pos = _skip_bytes_checked(data, pos, 4)
            count = _read_u32be(data, pos)
            pos = _skip_bytes_checked(data, pos + 4, count * 4)
        else:
            raise ValueError(f"Unsupported HUNK_EXT subtype {ext_type}")


def _skip_bytes_checked(data: bytes, pos: int, count: int) -> int:
    new_pos = pos + count
    if count < 0 or new_pos > len(data):
        raise ValueError("Unexpected EOF while parsing file layout")
    return new_pos


def _read_u16be(data: bytes, offset: int) -> int:
    if offset + 2 > len(data):
        raise ValueError("Unexpected EOF reading u16")
    return int.from_bytes(data[offset:offset + 2], "big")


def _read_u32be(data: bytes, offset: int) -> int:
    if offset + 4 > len(data):
        raise ValueError("Unexpected EOF reading u32")
    return _u32be(data, offset)


def _u16be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "big")


def _u32be(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "big")
