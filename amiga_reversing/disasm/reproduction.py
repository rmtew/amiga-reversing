from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
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
    reproduction_compare_rebuilt_bytes_with_c_backend_profile,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
    effective_metadata_hash,
)
from amiga_reversing.disasm.facts_v2_source_refusal import (
    FactsV2SourceRefused,
)
from amiga_reversing.disasm.oracle_compatibility import (
    oracle_compatibility_reports_for_options,
)
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    resolve_project_dir,
    resolve_project_paths,
)
from amiga_reversing.disasm.reproduction_report import (
    ReportContext,
    ReproductionOutcome,
    ReproductionReportStatus,
    RoundTripReportBuilder,
    direct_source_report_fields,
    direct_source_report_fields_from_ranges,
    profile_payload,
    row_int,
    row_match_text,
    row_str,
    write_report,
)
from amiga_reversing.disasm.reproduction_report import (
    issue as make_issue,
)
from amiga_reversing.disasm.source_rendering import (
    render_source_from_binary_source_or_raise,
)
from amiga_reversing.disasm.target_metadata import (
    TARGET_CORRECTIONS_FILE_NAME,
    TARGET_METADATA_FILE_NAME,
    TARGET_SEEDED_METADATA_FILE_NAME,
)
from amiga_reversing.disasm.tool_graph import capability_availability_for_modes
from amiga_reversing.disasm.workflow_profile import (
    WorkflowProfile,
    workflow_profile_payload,
)

REPRODUCTION_FILE_NAME = "reproduction.json"
FACTS_V2_DIRECT_SOURCE_COMPARE_ENV = "AMIGA_REVERSING_FACTS_V2_DIRECT_SOURCE_COMPARE"
MAX_DIFF_RANGES = 128
MAX_DIAGNOSTICS = 80


class ReproductionMode(StrEnum):
    EXACT = "exact"
    TEMPLATE_PRESERVED = "template_preserved"
    CANONICAL = "canonical"
    CONTENT = "content"
    SEMANTIC = "semantic"


class ReproductionContainerPolicy(StrEnum):
    ASSEMBLER_DEFAULT = "assembler_default"
    PRESERVE_ORIGINAL = "preserve_original"


class ReproductionRelocationPolicy(StrEnum):
    ASSEMBLER_DEFAULT = "assembler_default"
    PRESERVE_ORIGINAL_ENCODING = "preserve_original_encoding"


class ReproductionComparison(StrEnum):
    FULL_FILE = "full_file"
    CONTENT = "content"
    SEMANTIC = "semantic"


class ReproductionRequestedExactness(StrEnum):
    FULL_FILE = "full_file"
    CONTENT = "content"


class ReproductionFileShapeOrder(StrEnum):
    ASSEMBLER_DEFAULT = "assembler_default"
    MATCH_ORIGINAL = "match_original"


class ReproductionRelocationRecord(StrEnum):
    AUTO = "auto"
    LONG = "long"
    SHORT = "short"


REPRODUCTION_BACKENDS = {"auto", "amiga-hunk", "atari-st", "amiga-raw"}
REPRODUCTION_ANALYSIS_STAMP = "facts_v2"
REPRODUCTION_ASSEMBLERS = {"our"}
REPRODUCTION_ORACLE_MODES = {"vasm", "devpac"}
REPRODUCTION_CPUS = {"68000", "68010", "68020", "68030", "68040", "68060", "any"}
REPRODUCTION_MODES = frozenset(ReproductionMode)
REPRODUCTION_CONTAINER_POLICIES = frozenset(ReproductionContainerPolicy)
REPRODUCTION_RELOCATION_POLICIES = frozenset(ReproductionRelocationPolicy)
REPRODUCTION_COMPARISONS = frozenset(ReproductionComparison)
REPRODUCTION_REQUESTED_EXACTNESS = frozenset(ReproductionRequestedExactness)
REPRODUCTION_REQUESTED_EXACTNESS_IDS = {
    ReproductionRequestedExactness.FULL_FILE: 1,
    ReproductionRequestedExactness.CONTENT: 2,
}
_BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS: tuple[dict[str, object], ...] = (
    {
        "profile_id": "exact-framework",
        "name": "Exact framework gate",
        "workflow": "exactness_gate",
        "description": "Use the project renderer and assembler as the only exactness gate.",
        "options": {},
    },
    {
        "profile_id": "source-vasm",
        "name": "vasm source oracle",
        "workflow": "source_oracle",
        "description": "Keep the exactness gate on the framework and request vasm as an oracle workflow.",
        "options": {"oracle_modes": ["vasm"]},
    },
    {
        "profile_id": "source-devpac",
        "name": "GenAm/DevPac source oracle",
        "workflow": "source_oracle",
        "description": "Keep the exactness gate on the framework and request DevPac-compatible source oracle checks.",
        "options": {"oracle_modes": ["devpac"]},
    },
    {
        "profile_id": "content-semantic",
        "name": "Content semantic comparison",
        "workflow": "semantic_comparison",
        "description": "Compare rebuilt content semantics without changing the exact framework assembler gate.",
        "options": {
            "mode": "semantic",
            "comparison": "semantic",
            "requested_exactness": "content",
        },
    },
)
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


@dataclass(frozen=True, slots=True)
class DirectRebuildPhaseResult:
    rebuilt_bytes: bytes
    listing_profile: dict[str, object]
    direct_profile: dict[str, object]


@dataclass(frozen=True, slots=True)
class SourceRenderingPhaseResult:
    source_text: str
    listing_profile: dict[str, object]


@dataclass(frozen=True, slots=True)
class SourceAssemblyPhaseResult:
    rebuilt_bytes: bytes
    assembler_profile: dict[str, object]


@dataclass(frozen=True, slots=True)
class ReproductionComparisonPhaseResult:
    comparison: dict[str, object]
    c_profile: dict[str, object] | None


class RoundTripProfileTimings:
    def __init__(self, workflow_profile: WorkflowProfile) -> None:
        self._values: dict[str, object] = {}
        self._workflow_profile = workflow_profile

    def __setitem__(self, key: str, value: object) -> None:
        self._values[key] = value
        if isinstance(value, bool | int | float | str):
            self._workflow_profile.counters[key] = value

    def get(self, key: str) -> object:
        return self._values.get(key)

    def record(self, key: str, started_at: float) -> None:
        self[key] = round(time.perf_counter() - started_at, 4)

    def payload(self, started_at: float) -> dict[str, object]:
        return profile_payload(self._values, started_at)


def reproduction_report_path(target_dir: Path) -> Path:
    return target_dir / REPRODUCTION_FILE_NAME


def builtin_reproduction_profiles() -> list[dict[str, object]]:
    return [
        {
            key: value
            for key, value in definition.items()
            if key != "options"
        } | {"options": expand_reproduction_profile(str(definition["profile_id"]))}
        for definition in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS
    ]


def builtin_reproduction_profile(profile_id: str) -> dict[str, object]:
    for profile in builtin_reproduction_profiles():
        if profile.get("profile_id") == profile_id:
            return profile
    allowed = ", ".join(str(profile["profile_id"]) for profile in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS)
    raise ValueError(f"invalid reproduction profile id {profile_id!r}; expected one of {allowed}")


def expand_reproduction_profile(profile_id: str) -> dict[str, object]:
    for definition in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS:
        if definition.get("profile_id") != profile_id:
            continue
        raw_options = definition.get("options")
        payload = dict(cast(dict[str, object], raw_options)) if isinstance(raw_options, dict) else {}
        payload["profile_id"] = profile_id
        return validated_reproduction_options_payload(payload)
    allowed = ", ".join(str(profile["profile_id"]) for profile in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS)
    raise ValueError(f"invalid reproduction profile id {profile_id!r}; expected one of {allowed}")


def validated_reproduction_options_payload(payload: Mapping[str, object]) -> dict[str, object]:
    options = _default_reproduction_options()
    _merge_reproduction_options(options, dict(payload))
    reproduction_policy_for_options(options)
    return _json_ready_reproduction_options(options)


def write_target_reproduction_options(
    target_dir: Path,
    options: Mapping[str, object],
) -> dict[str, object]:
    path = target_dir / TARGET_METADATA_FILE_NAME
    payload = _read_json_object(path)
    if not payload:
        payload = _empty_target_metadata_payload()
    payload["reproduction"] = dict(options)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return dict(options)


def _empty_target_metadata_payload() -> dict[str, object]:
    return {
        "target_type": "program",
        "entry_register_seeds": [],
        "bootblock": None,
        "resident": None,
        "library": None,
        "custom_structs": [],
        "rsset_layout_regions": [],
        "seeded_entities": [],
        "seeded_code_labels": [],
        "seeded_code_entrypoints": [],
        "absolute_code_labels": [],
        "entry_comments": [],
        "manual_representations": [],
        "execution_views": [],
        "suppressed_seeded_items": [],
    }


def rebuilt_target_dir(target_name: str, *, project_root: Path = PROJECT_ROOT) -> Path:
    return project_root / "bin" / "rebuilt" / target_name


def run_direct_rebuild_phase(
    binary_source: BinarySource,
    *,
    metadata_path: Path,
    output_path: Path,
    compare_original: bool,
    project_root: Path,
) -> DirectRebuildPhaseResult:
    rebuilt_bytes, listing_profile, direct_profile = facts_v2_direct_rebuild_project_source_with_c_backend_profile(
        binary_source,
        metadata_path=metadata_path,
        output_path=output_path,
        compare_original=compare_original,
        project_root=project_root,
    )
    return DirectRebuildPhaseResult(rebuilt_bytes, listing_profile, direct_profile)


def run_source_rendering_phase(
    *,
    target_name: str,
    binary_source: BinarySource,
    target_dir: Path,
    metadata_path: Path,
    project_root: Path,
) -> SourceRenderingPhaseResult:
    rendering = render_source_from_binary_source_or_raise(
        target_id=target_name,
        binary_source=binary_source,
        target_dir=target_dir,
        metadata_path=metadata_path,
        project_root=project_root,
    )
    return SourceRenderingPhaseResult(rendering.source_text, rendering.listing_profile)


def run_source_assembly_phase(
    *,
    backend: str,
    source_text: str,
    include_dir: Path | None,
    output_path: Path | None = None,
    target_cpu: str,
    project_root: Path,
) -> SourceAssemblyPhaseResult:
    rebuilt_bytes, assembler_profile = assemble_platform_source_text_with_c_backend(
        backend,
        source_text,
        include_dir=include_dir if include_dir is not None and include_dir.exists() else None,
        output_path=output_path,
        target_cpu=target_cpu,
        project_root=project_root,
    )
    return SourceAssemblyPhaseResult(rebuilt_bytes, assembler_profile)


class RoundTripVerificationWorkflow:
    def run(
        self,
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
        workflow_profile = WorkflowProfile("round_trip_verification", target_id=target_name)
        profile_started_at = time.perf_counter()
        round_trip_profile = RoundTripProfileTimings(workflow_profile)
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
        report_builder = RoundTripReportBuilder(
            ReportContext(
                target_name=target_name,
                started_at=started_at,
                input_stamp=input_stamp,
                assembler=assembler,
                backend=backend,
                source_path=source_path,
                rebuilt_path=rebuilt_path,
            )
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
            paths = resolve_project_paths(target_name, project_root=project_root)
            target_dir = paths.target_dir
            input_stamp = reproduction_input_stamp(target_name, project_root=project_root, assembler=assembler)
            workflow_profile.input_stamp = dict(input_stamp)
            backend = cast(str, input_stamp["backend"])
            assembler = cast(str, input_stamp["assembler"])
            assembler_cpu = cast(str, input_stamp["assembler_cpu"])
            report_builder = RoundTripReportBuilder(
                ReportContext(
                    target_name=target_name,
                    started_at=started_at,
                    input_stamp=input_stamp,
                    assembler=assembler,
                    backend=backend,
                    source_path=source_path,
                    rebuilt_path=rebuilt_path,
                )
            )
            _record_profile_timing(round_trip_profile, "prepare_seconds", phase_started_at)
            out_dir.mkdir(parents=True, exist_ok=True)
            if assembler not in REPRODUCTION_ASSEMBLERS:
                message = f"unsupported exactness assembler: {assembler}"
                report = report_builder.error(
                    status=ReproductionReportStatus.TOOL_ERROR,
                    tool_error=message,
                    issues=[make_issue("tool", message, None)],
                )
                return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
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
                    metadata_file = cast(Path, metadata_path)
                    try:
                        direct_result = run_direct_rebuild_phase(
                            paths.binary_source,
                            metadata_path=metadata_file,
                            output_path=rebuilt_path,
                            compare_original=use_facts_v2_direct_compare,
                            project_root=project_root,
                        )
                        direct_bytes = direct_result.rebuilt_bytes
                        listing_profile = direct_result.listing_profile
                        direct_profile = direct_result.direct_profile
                        rebuilt_bytes = direct_bytes
                        direct_rebuild_for_reproduction = True
                        _merge_direct_rebuild_profile(round_trip_profile, direct_profile)
                        _record_profile_timing(round_trip_profile, "direct_rebuild_seconds", phase_started_at)
                        workflow_profile.add_span(
                            "direct_rebuild",
                            _profile_timing_value(round_trip_profile, "direct_rebuild_seconds"),
                            module="c_backend",
                            detail={"profile": direct_profile},
                        )
                        round_trip_profile["render_seconds"] = _profile_timing_total(listing_profile)
                        round_trip_profile["assemble_seconds"] = 0.0
                        round_trip_profile["facts_v2_direct_rebuild_c_api"] = 1.0
                        source_size = _facts_v2_profile_source_bytes(listing_profile)
                        round_trip_profile["source_file_rewritten"] = 0.0
                        round_trip_profile["write_source_seconds"] = 0.0
                        if facts_v2_direct_source_compare_enabled():
                            include_dir = _include_dir_for_backend(backend, project_root)
                            compare_started_at = time.perf_counter()
                            source_compare_rendering = run_source_rendering_phase(
                                target_name=target_name,
                                binary_source=paths.binary_source,
                                target_dir=paths.target_dir,
                                metadata_path=metadata_file,
                                project_root=project_root,
                            )
                            rendered_source_text = source_compare_rendering.source_text
                            source_compare_profile = source_compare_rendering.listing_profile
                            source_assembly = run_source_assembly_phase(
                                backend=backend,
                                source_text=rendered_source_text,
                                include_dir=include_dir,
                                target_cpu=assembler_cpu,
                                project_root=project_root,
                            )
                            source_bytes = source_assembly.rebuilt_bytes
                            assembler_profile = source_assembly.assembler_profile
                            if listing_profile is None:
                                listing_profile = source_compare_profile
                            _merge_assembler_profile(round_trip_profile, assembler_profile)
                            _record_profile_timing(
                                round_trip_profile,
                                "facts_v2_direct_source_compare_seconds",
                                compare_started_at,
                            )
                            original_for_source_compare = paths.binary_source.read_bytes()
                            source_compare_profile = reproduction_compare_rebuilt_bytes_with_c_backend_profile(
                                paths.binary_source,
                                source_bytes,
                                metadata_path=metadata_path,
                                project_root=project_root,
                            )
                            _record_direct_source_comparison(
                                round_trip_profile,
                                direct_bytes,
                                source_bytes,
                                compare_profile=source_compare_profile,
                            )
                            direct_source_report = direct_source_report_fields(
                                original_for_source_compare,
                                source_bytes,
                                assembler=assembler,
                            )
                            if direct_bytes != source_bytes:
                                round_trip_profile["facts_v2_direct_source_mismatch"] = 1.0
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
                            round_trip_profile["facts_v2_direct_exact_fast_path"] = 1.0 if direct_full_exact else 0.0
                            if not direct_full_exact:
                                round_trip_profile["facts_v2_direct_semantic_fast_path"] = 1.0
                            round_trip_profile["diff_phase_seconds"] = 0.0
                            workflow_profile.add_span(
                                "reproduction_compare",
                                0.0,
                                module="c_backend",
                                detail={"profile": direct_profile, "mode": "direct_rebuild_compare"},
                            )
                            original_size = _optional_int(input_stamp.get("original_size"), len(direct_bytes))
                            direct_shape_diagnostics = _direct_compare_shape_diagnostics(
                                direct_profile, row_for_section_offset
                            )
                            direct_shape_row_issues = _direct_compare_shape_row_issues(
                                direct_profile, row_for_section_offset
                            )
                            report = report_builder.completed(
                                ReproductionOutcome(
                                    status=(
                                        ReproductionReportStatus.EXACT
                                        if selected_exact
                                        else ReproductionReportStatus.BINARY_MISMATCH
                                    ),
                                    exact=selected_exact,
                                    original_size=original_size,
                                    rebuilt_size=len(direct_bytes),
                                    rebuilt_sha256=digest,
                                    canonical_rebuilt_size=len(direct_bytes),
                                    canonical_rebuilt_sha256=digest,
                                    canonical_rebuilt_path=rebuilt_path,
                                    first_diff=None,
                                    diff_ranges=[],
                                    canonical_diff_ranges=[],
                                    file_layout=[],
                                    row_mappings=direct_shape_row_issues,
                                    issues=direct_shape_row_issues,
                                    assembler_diagnostics=[],
                                    assembler_stdout=assembler_stdout,
                                    assembler_stderr=assembler_stderr,
                                    file_shape_adjustments=[],
                                    file_shape_diagnostics=direct_shape_diagnostics,
                                    canonical_file_shape_diagnostics=[
                                        dict(item) for item in direct_shape_diagnostics
                                    ],
                                    comparison=comparison,
                                    direct_source_report=direct_source_report,
                                    listing_profile=listing_profile,
                                    profile=round_trip_profile.payload(profile_started_at) if profile else None,
                                    workflow_profile=workflow_profile_payload(workflow_profile),
                                )
                            )
                            return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                    except FactsV2SourceRefused as exc:
                        message = str(exc)
                        _record_profile_timing(round_trip_profile, "direct_rebuild_seconds", phase_started_at)
                        workflow_profile.add_span(
                            "direct_rebuild",
                            _profile_timing_value(round_trip_profile, "direct_rebuild_seconds"),
                            module="c_backend",
                            detail={"listing_profile": exc.listing_profile, "status": "source_refused"},
                        )
                        round_trip_profile["render_seconds"] = _profile_timing_total(exc.listing_profile)
                        round_trip_profile["assemble_seconds"] = 0.0
                        round_trip_profile["facts_v2_direct_rebuild_c_api"] = 1.0
                        report = report_builder.error(
                            status=ReproductionReportStatus.RENDER_ERROR,
                            tool_error=message,
                            issues=[make_issue("renderer", message, None)],
                            listing_profile=exc.listing_profile,
                            profile=round_trip_profile.payload(profile_started_at) if profile else None,
                            workflow_profile=workflow_profile_payload(workflow_profile),
                        )
                        return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                    except FactsV2DirectRebuildRefused as exc:
                        listing_profile = exc.source_profile
                        _merge_direct_rebuild_profile(round_trip_profile, exc.direct_profile)
                        _record_profile_timing(round_trip_profile, "direct_rebuild_seconds", phase_started_at)
                        workflow_profile.add_span(
                            "direct_rebuild",
                            _profile_timing_value(round_trip_profile, "direct_rebuild_seconds"),
                            module="c_backend",
                            detail={"profile": exc.direct_profile, "status": "direct_rebuild_refused"},
                        )
                        round_trip_profile["facts_v2_direct_rebuild_c_api"] = 1.0
                        message = f"facts_v2 direct rebuild refused: {exc}"
                        accepted_kind = _accepted_direct_rebuild_refusal_kind(
                            backend,
                            source_profile=listing_profile,
                            direct_profile=exc.direct_profile,
                        )
                        if accepted_kind is not None:
                            report = report_builder.error(
                                status=ReproductionReportStatus.ACCEPTED_MISMATCH,
                                issues=[],
                                listing_profile=listing_profile,
                                direct_rebuild_profile=exc.direct_profile,
                                profile=round_trip_profile.payload(profile_started_at) if profile else None,
                                workflow_profile=workflow_profile_payload(workflow_profile),
                                extra={
                                    "accepted_mismatch_kind": accepted_kind,
                                    "accepted_mismatch_reason": message,
                                },
                            )
                            return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                        report = report_builder.error(
                            status=ReproductionReportStatus.TOOL_ERROR,
                            tool_error=message,
                            issues=[make_issue("direct_rebuild", message, None)],
                            listing_profile=listing_profile,
                            direct_rebuild_profile=exc.direct_profile,
                            profile=round_trip_profile.payload(profile_started_at) if profile else None,
                            workflow_profile=workflow_profile_payload(workflow_profile),
                        )
                        return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                    except FactsV2ProfiledOperationFailed as exc:
                        listing_profile = exc.source_profile
                        _merge_direct_rebuild_profile(round_trip_profile, exc.operation_profile)
                        _record_profile_timing(round_trip_profile, "direct_rebuild_seconds", phase_started_at)
                        workflow_profile.add_span(
                            "direct_rebuild",
                            _profile_timing_value(round_trip_profile, "direct_rebuild_seconds"),
                            module="c_backend",
                            detail={"profile": exc.operation_profile, "status": "operation_failed"},
                        )
                        round_trip_profile["facts_v2_direct_rebuild_c_api"] = 1.0
                        message = str(exc)
                        report = report_builder.error(
                            status=ReproductionReportStatus.TOOL_ERROR,
                            tool_error=message,
                            issues=[make_issue("direct_rebuild", message, None)],
                            listing_profile=listing_profile,
                            direct_rebuild_profile=exc.operation_profile,
                            profile=round_trip_profile.payload(profile_started_at) if profile else None,
                            workflow_profile=workflow_profile_payload(workflow_profile),
                        )
                        return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
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
                    metadata_file = cast(Path, metadata_path)
                    try:
                        rendering = run_source_rendering_phase(
                            target_name=target_name,
                            binary_source=paths.binary_source,
                            target_dir=paths.target_dir,
                            metadata_path=metadata_file,
                            project_root=project_root,
                        )
                        rendered_source_text = rendering.source_text
                        listing_profile = rendering.listing_profile
                    except FactsV2SourceRefused as exc:
                        message = str(exc)
                        _record_profile_timing(round_trip_profile, "render_source_seconds", phase_started_at)
                        round_trip_profile["render_seconds"] = _profile_timing_total(exc.listing_profile)
                        round_trip_profile["assemble_seconds"] = 0.0
                        round_trip_profile["listing_artifact_source_assembly"] = 1.0
                        report = report_builder.error(
                            status=ReproductionReportStatus.RENDER_ERROR,
                            tool_error=message,
                            issues=[make_issue("renderer", message, None)],
                            listing_profile=exc.listing_profile,
                            profile=round_trip_profile.payload(profile_started_at) if profile else None,
                        )
                        return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                    _record_profile_timing(round_trip_profile, "render_source_seconds", phase_started_at)
                    round_trip_profile["render_seconds"] = _profile_timing_total(listing_profile)
                    source_size = _facts_v2_profile_source_bytes(listing_profile)
                    phase = "assemble"
                    phase_started_at = time.perf_counter()
                    try:
                        assembly = run_source_assembly_phase(
                            backend=backend,
                            source_text=rendered_source_text,
                            include_dir=include_dir,
                            output_path=rebuilt_path,
                            target_cpu=assembler_cpu,
                            project_root=project_root,
                        )
                        rebuilt_bytes = assembly.rebuilt_bytes
                        assembler_profile = assembly.assembler_profile
                        _merge_assembler_profile(round_trip_profile, assembler_profile)
                        assembled_source_for_reproduction = True
                    except RuntimeError as exc:
                        assembler_stderr = str(exc)
                        _record_profile_timing(round_trip_profile, "assemble_seconds", phase_started_at)
                        round_trip_profile["listing_artifact_source_assembly"] = 1.0
                        diagnostics = parse_assembler_diagnostics(assembler_stderr)
                        report = report_builder.error(
                            status=ReproductionReportStatus.ASSEMBLER_ERROR,
                            issues=diagnostics or [make_issue("assembler", "Assembler failed", None)],
                            assembler_diagnostics=diagnostics,
                            assembler_stdout=assembler_stdout,
                            assembler_stderr=assembler_stderr,
                            listing_profile=listing_profile,
                            profile=round_trip_profile.payload(profile_started_at) if profile else None,
                        )
                        return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                _record_profile_timing(round_trip_profile, "assemble_seconds", phase_started_at)
                round_trip_profile["assemble_seconds"] = _flat_profile_total(assembler_profile)
                round_trip_profile["listing_artifact_source_assembly"] = 1.0
                round_trip_profile["source_file_rewritten"] = 0.0
                round_trip_profile["write_source_seconds"] = 0.0
            elif source_text is not None:
                round_trip_profile["render_seconds"] = (
                    _profile_timing_total(listing_profile) if listing_profile is not None else 0.0
                )
                round_trip_profile["reused_source_text"] = 1.0
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
                source_size = _write_source_artifact(source_path, source_text, round_trip_profile)
            else:
                round_trip_profile["source_file_rewritten"] = 0.0
                round_trip_profile["write_source_seconds"] = 0.0

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
                    assembly = run_source_assembly_phase(
                        backend=backend,
                        source_text=source_text,
                        include_dir=include_dir,
                        output_path=rebuilt_path,
                        target_cpu=assembler_cpu,
                        project_root=project_root,
                    )
                    rebuilt_bytes = assembly.rebuilt_bytes
                    assembler_profile = assembly.assembler_profile
                    _merge_assembler_profile(round_trip_profile, assembler_profile)
                    assembled_source_for_reproduction = True
                except RuntimeError as exc:
                    assembler_stderr = str(exc)
                    _record_profile_timing(round_trip_profile, "assemble_seconds", phase_started_at)
                    diagnostics = parse_assembler_diagnostics(assembler_stderr)
                    report = report_builder.error(
                        status=ReproductionReportStatus.ASSEMBLER_ERROR,
                        issues=diagnostics or [make_issue("assembler", "Assembler failed", None)],
                        assembler_diagnostics=diagnostics,
                        assembler_stdout=assembler_stdout,
                        assembler_stderr=assembler_stderr,
                        profile=round_trip_profile.payload(profile_started_at) if profile else None,
                    )
                    return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
                _record_profile_timing(round_trip_profile, "assemble_seconds", phase_started_at)
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
            _record_profile_timing(round_trip_profile, "read_original_seconds", read_original_started_at)
            canonical_rebuilt = rebuilt_bytes
            round_trip_profile["read_rebuilt_seconds"] = 0.0
            round_trip_profile["reused_assembler_rebuilt_bytes"] = 1.0
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
            _record_profile_timing(round_trip_profile, "file_shape_policy_seconds", policy_started_at)
            diff_started_at = time.perf_counter()
            diff_ranges = grouped_diff_ranges(original, rebuilt)
            canonical_diff_ranges = (
                diff_ranges
                if not file_shape_adjustments or rebuilt is canonical_rebuilt
                else grouped_diff_ranges(original, canonical_rebuilt)
            )
            first_diff_payload = _first_diff_from_ranges(original, rebuilt, diff_ranges)
            _record_profile_timing(round_trip_profile, "diff_seconds", diff_started_at)
            if not diff_ranges and not canonical_diff_ranges:
                file_layout: list[dict[str, object]] = []
                row_issues: list[dict[str, object]] = []
                file_shape_diagnostics: list[dict[str, object]] = []
                canonical_file_shape_diagnostics: list[dict[str, object]] = []
                round_trip_profile["file_layout_seconds"] = 0.0
                round_trip_profile["row_mapping_seconds"] = 0.0
                compare_started_at = time.perf_counter()
                comparison_phase = run_reproduction_comparison_phase(
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
                comparison = comparison_phase.comparison
                c_compare_profile = comparison_phase.c_profile
                compare_detail: dict[str, object] = (
                    {"profile": c_compare_profile} if c_compare_profile is not None else {"backend": backend}
                )
                workflow_profile.add_span(
                    "reproduction_compare",
                    time.perf_counter() - compare_started_at,
                    module="c_backend" if c_compare_profile is not None else "python",
                    detail=compare_detail,
                )
                if c_compare_profile is not None:
                    _merge_source_compare_profile(round_trip_profile, c_compare_profile)
            else:
                compare_started_at = time.perf_counter()
                comparison_phase = run_reproduction_comparison_phase(
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
                    file_layout=[],
                )
                comparison = comparison_phase.comparison
                c_compare_profile = comparison_phase.c_profile
                compare_detail = (
                    {"profile": c_compare_profile} if c_compare_profile is not None else {"backend": backend}
                )
                workflow_profile.add_span(
                    "reproduction_compare",
                    time.perf_counter() - compare_started_at,
                    module="c_backend" if c_compare_profile is not None else "python",
                    detail=compare_detail,
                )
                layout_started_at = time.perf_counter()
                file_layout = _comparison_profile_file_layout(c_compare_profile, "reproduction_compare")
                if not file_layout and backend == "amiga-raw":
                    file_layout = file_layout_for_binary_source(paths.binary_source, backend=backend, data=original)
                _record_profile_timing(round_trip_profile, "file_layout_seconds", layout_started_at)
                if c_compare_profile is not None:
                    _merge_source_compare_profile(round_trip_profile, c_compare_profile)
                row_mapping_started_at = time.perf_counter()
                row_issues = diff_issues_for_lookup(
                    diff_ranges,
                    row_for_section_offset,
                    file_layout=file_layout,
                )
                _record_profile_timing(round_trip_profile, "row_mapping_seconds", row_mapping_started_at)
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
                if c_compare_profile is not None:
                    c_shape_diagnostics = _comparison_profile_shape_diagnostics(
                        c_compare_profile, "reproduction_compare"
                    )
                    if c_shape_diagnostics:
                        file_shape_diagnostics = c_shape_diagnostics
                        canonical_file_shape_diagnostics = [dict(item) for item in c_shape_diagnostics]
                    direct_shape_diagnostics = _reproduction_compare_shape_diagnostics(
                        c_compare_profile, row_for_section_offset
                    )
                    if direct_shape_diagnostics:
                        file_shape_diagnostics = direct_shape_diagnostics
                        canonical_file_shape_diagnostics = [dict(item) for item in direct_shape_diagnostics]
            if direct_source_report is None and assembled_source_for_reproduction:
                direct_source_report = direct_source_report_fields_from_ranges(
                    original,
                    canonical_rebuilt,
                    assembler=assembler,
                    diff_ranges=canonical_diff_ranges,
                )
            _record_profile_timing(round_trip_profile, "diff_phase_seconds", phase_started_at)
            exact = bool(comparison.get("full_file_exact"))
            report_status = ReproductionReportStatus.EXACT if exact else ReproductionReportStatus.BINARY_MISMATCH
            comparison_status = comparison.get("status")
            selected_comparison = _require_reproduction_enum_option(
                reproduction_policy, "comparison", ReproductionComparison
            )
            if (
                comparison_status == ReproductionReportStatus.CONTENT_MATCH
                and selected_comparison is ReproductionComparison.CONTENT
            ):
                report_status = ReproductionReportStatus.CONTENT_MATCH
            elif (
                comparison_status == ReproductionReportStatus.SEMANTIC_MATCH
                and selected_comparison is ReproductionComparison.SEMANTIC
            ):
                report_status = ReproductionReportStatus.SEMANTIC_MATCH
            if rebuilt != canonical_rebuilt:
                canonical_rebuilt_path.write_bytes(canonical_rebuilt)
                rebuilt_path.write_bytes(rebuilt)
            canonical_path_for_report = canonical_rebuilt_path if rebuilt != canonical_rebuilt else rebuilt_path
            report = report_builder.completed(
                ReproductionOutcome(
                    status=report_status,
                    exact=exact,
                    original_size=len(original),
                    rebuilt_size=len(rebuilt),
                    rebuilt_sha256=_sha256_bytes(rebuilt),
                    canonical_rebuilt_size=len(canonical_rebuilt),
                    canonical_rebuilt_sha256=_sha256_bytes(canonical_rebuilt),
                    canonical_rebuilt_path=canonical_path_for_report,
                    first_diff=first_diff_payload,
                    diff_ranges=diff_ranges,
                    canonical_diff_ranges=canonical_diff_ranges,
                    file_layout=file_layout,
                    row_mappings=row_issues,
                    issues=row_issues,
                    assembler_diagnostics=diagnostics,
                    assembler_stdout=assembler_stdout,
                    assembler_stderr=assembler_stderr,
                    file_shape_adjustments=file_shape_adjustments,
                    file_shape_diagnostics=file_shape_diagnostics,
                    canonical_file_shape_diagnostics=canonical_file_shape_diagnostics,
                    comparison=comparison,
                    direct_source_report=direct_source_report,
                    listing_profile=listing_profile,
                    profile=round_trip_profile.payload(profile_started_at) if profile else None,
                    workflow_profile=workflow_profile_payload(workflow_profile),
                )
            )
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
            return _write_reproduction_report(paths.target_dir, report, project_root=project_root)
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
                report_builder = RoundTripReportBuilder(
                    ReportContext(
                        target_name=target_name,
                        started_at=started_at,
                        input_stamp=input_stamp,
                        assembler=assembler,
                        backend=str(input_stamp.get("backend") or backend),
                        source_path=source_path,
                        rebuilt_path=rebuilt_path,
                    )
                )
            status = (
                ReproductionReportStatus.RENDER_ERROR
                if phase == "render"
                else ReproductionReportStatus.TOOL_ERROR
            )
            issue_kind = "renderer" if phase == "render" else "tool"
            report = report_builder.error(
                status=status,
                tool_error=str(exc),
                issues=[make_issue(issue_kind, str(exc), None)],
                profile=round_trip_profile.payload(profile_started_at) if profile else None,
                workflow_profile=workflow_profile_payload(workflow_profile),
            )
            if target_dir is None:
                return report
            return _write_reproduction_report(target_dir, report, project_root=project_root)


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
    return RoundTripVerificationWorkflow().run(
        target_name,
        project_root=project_root,
        assembler=assembler,
        progress_callback=progress_callback,
        profile=profile,
        pre_rendered_source_text=pre_rendered_source_text,
        pre_rendered_source_profile=pre_rendered_source_profile,
        row_for_section_offset=row_for_section_offset,
        source_assembly_debug=source_assembly_debug,
    )


def load_reproduction_report(
    target_name: str,
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    resolve_error: Exception | None = None
    target_dir: Path | None = None
    try:
        paths = resolve_project_paths(target_name, project_root=project_root)
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
            "status": ReproductionReportStatus.NOT_READY,
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
    paths = resolve_project_paths(target_name, project_root=project_root)
    options = reproduction_options_for_target(paths.target_dir)
    backend = _effective_reproduction_backend(backend_for_binary_source(paths.binary_source), options)
    assembler = _effective_reproduction_assembler(assembler, options)
    assembler_cpu = _effective_reproduction_cpu(options)
    reproduction_policy = reproduction_policy_for_options(options)
    oracle_tool_availability = oracle_tool_availability_for_options(options, project_root=project_root)
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
        "oracle_tool_availability": oracle_tool_availability,
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


def oracle_tool_availability_for_options(
    options: Mapping[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, object]]:
    oracle_modes = options.get("oracle_modes")
    if not isinstance(oracle_modes, list) or not oracle_modes:
        return []
    return capability_availability_for_modes(oracle_modes, project_root=project_root)


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
    oracle_tool_availability = oracle_tool_availability_for_options(options, project_root=project_root)
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
        "oracle_tool_availability": oracle_tool_availability,
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
    mode = _require_reproduction_enum_option(policy, "mode", ReproductionMode)
    comparison_mode = _require_reproduction_enum_option(policy, "comparison", ReproductionComparison)
    requested_exactness = _require_reproduction_enum_option(
        policy, "requested_exactness", ReproductionRequestedExactness
    )
    requested_exactness_id = _require_requested_exactness_id(policy, requested_exactness)
    if full_file_exact and canonical_full_file_exact:
        return {
            "mode": mode,
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
        "mode": mode,
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
    return _c_profile_reproduction_comparison(
        backend,
        policy,
        direct_profile,
        prefix="direct_compare",
        full_file_exact_key="direct_rebuild_exact",
        content_exact_key="direct_compare_semantic_exact",
    )


def _reproduction_compare_reproduction_comparison(
    backend: str,
    policy: dict[str, object],
    compare_profile: dict[str, object],
) -> dict[str, object]:
    return _c_profile_reproduction_comparison(
        backend,
        policy,
        compare_profile,
        prefix="reproduction_compare",
        full_file_exact_key="reproduction_compare_full_file_exact",
        content_exact_key="reproduction_compare_content_exact",
    )


def _c_profile_reproduction_comparison(
    backend: str,
    policy: dict[str, object],
    compare_profile: dict[str, object],
    *,
    prefix: str,
    full_file_exact_key: str,
    content_exact_key: str,
) -> dict[str, object]:
    mode = _require_reproduction_enum_option(policy, "mode", ReproductionMode)
    comparison_mode = _require_reproduction_enum_option(policy, "comparison", ReproductionComparison)
    requested_exactness = _require_reproduction_enum_option(
        policy, "requested_exactness", ReproductionRequestedExactness
    )
    requested_exactness_id = _require_requested_exactness_id(policy, requested_exactness)
    status_id = _direct_profile_int(compare_profile, f"{prefix}_status_id")
    exactness_id = _direct_profile_int(compare_profile, f"{prefix}_exactness_id")
    issue_flags = _direct_profile_int(compare_profile, f"{prefix}_issue_group_flags") or 0
    full_file_exact = bool(exactness_id == 1 or compare_profile.get(full_file_exact_key) is True)
    semantic_exact = bool(exactness_id in {1, 2} or compare_profile.get(content_exact_key) is True)
    content_exact_accepted = bool(semantic_exact and requested_exactness_id >= 2)
    selected_exact = bool(full_file_exact or content_exact_accepted)
    payload_exact = bool(semantic_exact or compare_profile.get(f"{prefix}_payload_exact") is True)
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
        "mode": mode,
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
    return _c_compare_shape_diagnostics(
        direct_profile, "direct_compare", "facts_v2_direct_compare", row_for_section_offset
    )


def _reproduction_compare_shape_diagnostics(
    compare_profile: dict[str, object],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None = None,
) -> list[dict[str, object]]:
    return _c_compare_shape_diagnostics(
        compare_profile, "reproduction_compare", "facts_v2_reproduction_compare", row_for_section_offset
    )


def _c_compare_shape_diagnostics(
    compare_profile: dict[str, object],
    prefix: str,
    source: str,
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None = None,
) -> list[dict[str, object]]:
    issue_flags = _direct_profile_int(compare_profile, f"{prefix}_issue_group_flags") or 0
    issue_kinds = _c_compare_issue_labels(issue_flags, _C_COMPARE_FILE_STRUCTURE_ISSUE_FLAGS)
    if issue_kinds:
        diagnostics: list[dict[str, object]] = [{"kind": issue_kind, "group": "original_file_structure", "source": source}
            for issue_kind in issue_kinds]
        _attach_c_compare_source_hints(diagnostics, compare_profile, f"{prefix}_source_hints", row_for_section_offset)
        return diagnostics
    if compare_profile.get(f"{prefix}_container_oddity") is not True:
        return []
    return [
        {
            "kind": "container_shape_oddity",
            "source": source,
            "status": compare_profile.get(f"{prefix}_status") or "semantic_container_oddity",
        }
    ]


def _attach_direct_compare_source_hints(
    diagnostics: list[dict[str, object]],
    direct_profile: dict[str, object],
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
) -> None:
    _attach_c_compare_source_hints(diagnostics, direct_profile, "direct_compare_source_hints", row_for_section_offset)


def _attach_c_compare_source_hints(
    diagnostics: list[dict[str, object]],
    compare_profile: dict[str, object],
    hints_key: str,
    row_for_section_offset: Callable[[int | None, int], Mapping[str, object] | None] | None,
) -> None:
    if row_for_section_offset is None:
        return
    hints = compare_profile.get(hints_key)
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
            diagnostic["addr"] = row_int(row, "addr")
            diagnostic["stable_key"] = row_str(row, "stable_key")
            diagnostic["match_text"] = row_match_text(row)
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
            make_issue(
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
        return _reproduction_compare_reproduction_comparison(backend, policy, direct_profile), direct_profile
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


def run_reproduction_comparison_phase(
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
) -> ReproductionComparisonPhaseResult:
    comparison, c_profile = _comparison_for_rebuilt_bytes(
        binary_source,
        rebuilt,
        backend=backend,
        policy=policy,
        metadata_path=metadata_path,
        project_root=project_root,
        original=original,
        canonical_rebuilt=canonical_rebuilt,
        diff_ranges=diff_ranges,
        canonical_diff_ranges=canonical_diff_ranges,
        file_layout=file_layout,
    )
    return ReproductionComparisonPhaseResult(comparison, c_profile)


def _comparison_profile_file_layout(
    profile: dict[str, object] | None,
    prefix: str,
) -> list[dict[str, object]]:
    if profile is None:
        return []
    return [dict(item) for item in _dict_list(profile.get(f"{prefix}_file_layout"))]


def _comparison_profile_shape_diagnostics(
    profile: dict[str, object] | None,
    prefix: str,
) -> list[dict[str, object]]:
    if profile is None:
        return []
    diagnostics: list[dict[str, object]] = []
    for item in _dict_list(profile.get(f"{prefix}_file_shape_diagnostics")):
        diagnostic = dict(item)
        diagnostic.setdefault("group", "original_file_structure")
        diagnostic.setdefault("source", "facts_v2_reproduction_compare")
        diagnostics.append(diagnostic)
    return diagnostics[:MAX_DIAGNOSTICS]


def _merge_source_compare_profile(timings: RoundTripProfileTimings, profile: dict[str, object]) -> None:
    for key, value in profile.items():
        if key == "facts_v2_reproduction_compare":
            output_key = "facts_v2_source_reproduction_compare_c_api"
        elif key.startswith("reproduction_compare_"):
            output_key = f"facts_v2_source_{key}"
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
    del original, rebuilt, backend, diff_ranges, file_layout
    return []


def file_layout_for_binary_source(
    binary_source: BinarySource,
    *,
    backend: str,
    data: bytes | None = None,
) -> list[dict[str, object]]:
    payload = binary_source.read_bytes() if data is None else data
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
            issues.append(make_issue("diff", _diff_summary(diff_range), row, diff_range=diff_range))
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
                make_issue(
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
    row_index = row_int(row, "row_index")
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
        diagnostics.append(make_issue("assembler", stripped, row))
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


def _write_reproduction_report(
    target_dir: Path,
    report: dict[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    report = _report_with_oracle_compatibility(report, project_root=project_root)
    return write_report(reproduction_report_path(target_dir), report)


def _report_with_oracle_compatibility(
    report: dict[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    input_stamp = report.get("input_stamp")
    if not isinstance(input_stamp, dict):
        return report
    options = input_stamp.get("reproduction_options")
    if not isinstance(options, dict):
        return report
    oracle_modes = options.get("oracle_modes")
    if not isinstance(oracle_modes, list) or not oracle_modes:
        return report
    payload = dict(report)
    payload["oracle_compatibility"] = oracle_compatibility_reports_for_options(
        str(report.get("target") or ""),
        options,
        project_root=project_root,
    )
    return payload


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


def _write_source_artifact(path: Path, text: str, round_trip_profile: RoundTripProfileTimings) -> int:
    started_at = time.perf_counter()
    source_size, source_written = _write_text_if_changed(path, text)
    round_trip_profile["source_file_rewritten"] = 1.0 if source_written else 0.0
    _record_profile_timing(round_trip_profile, "write_source_seconds", started_at)
    return source_size


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
    timings: RoundTripProfileTimings,
    key: str,
    started_at: float,
) -> None:
    timings.record(key, started_at)


def _profile_timing_value(timings: RoundTripProfileTimings, key: str) -> float:
    value = timings.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def _merge_assembler_profile(timings: RoundTripProfileTimings, profile: dict[str, object]) -> None:
    for key, value in profile.items():
        if isinstance(value, bool):
            timings[f"assembler_{key}"] = 1.0 if value else 0.0
        elif key.endswith("_bytes") and isinstance(value, int):
            timings[f"assembler_{key}"] = value
        elif isinstance(value, (int, float)):
            timings[f"assembler_{key}"] = round(float(value), 6)


def _merge_direct_rebuild_profile(timings: RoundTripProfileTimings, profile: dict[str, object]) -> None:
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
    timings: RoundTripProfileTimings,
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
    exactness_id = _direct_profile_int(compare_profile, "reproduction_compare_exactness_id") or 0
    timings["facts_v2_source_full_file_exact"] = 1.0 if exactness_id == 1 else 0.0
    timings["facts_v2_source_content_exact"] = 1.0 if exactness_id in {1, 2} else 0.0
    timings["facts_v2_source_payload_exact"] = (
        1.0 if compare_profile.get("reproduction_compare_payload_exact") is True else 0.0
    )
    if "reproduction_compare_relocation_semantics_exact" in compare_profile:
        timings["facts_v2_source_relocation_semantics_exact"] = (
            1.0 if compare_profile.get("reproduction_compare_relocation_semantics_exact") is True else 0.0
        )
    if "reproduction_compare_status_id" in compare_profile:
        timings["facts_v2_source_compare_status_id"] = _direct_profile_int(
            compare_profile, "reproduction_compare_status_id"
        ) or 0
    if "reproduction_compare_issue_group_flags" in compare_profile:
        timings["facts_v2_source_compare_issue_group_flags"] = _direct_profile_int(
            compare_profile, "reproduction_compare_issue_group_flags"
        ) or 0


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


def _default_reproduction_options() -> dict[str, object]:
    return {
        "profile_id": "exact-framework",
        "mode": ReproductionMode.EXACT,
        "assembler": "our",
        "cpu": "any",
        "backend": "auto",
        "include_dirs": "auto",
        "oracle_modes": [],
        "container_policy": ReproductionContainerPolicy.PRESERVE_ORIGINAL,
        "relocation_policy": ReproductionRelocationPolicy.PRESERVE_ORIGINAL_ENCODING,
        "comparison": ReproductionComparison.FULL_FILE,
        "requested_exactness": ReproductionRequestedExactness.FULL_FILE,
        "requested_exactness_id": 1,
        "file_shape": {
            "relocation_order": ReproductionFileShapeOrder.MATCH_ORIGINAL,
            "relocation_record": ReproductionRelocationRecord.AUTO,
            "section_aux_order": ReproductionFileShapeOrder.ASSEMBLER_DEFAULT,
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
    return payloads


def _merge_reproduction_options(options: dict[str, object], payload: dict[str, object]) -> None:
    if "profile_id" not in payload and any(
        key in payload
        for key in (
            "mode",
            "assembler",
            "cpu",
            "backend",
            "include_dirs",
            "oracle_modes",
            "container_policy",
            "relocation_policy",
            "comparison",
            "requested_exactness",
            "file_shape",
            "raw_output",
        )
    ):
        options["profile_id"] = None
    if "profile_id" in payload:
        profile_id = payload["profile_id"]
        if profile_id is None:
            options["profile_id"] = None
        elif isinstance(profile_id, str) and any(
            profile.get("profile_id") == profile_id for profile in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS
        ):
            options["profile_id"] = profile_id
        else:
            allowed = ", ".join(str(profile["profile_id"]) for profile in _BUILTIN_REPRODUCTION_PROFILE_DEFINITIONS)
            raise ValueError(f"invalid reproduction profile id {profile_id!r}; expected one of {allowed}")
    mode = _parse_reproduction_enum_field(payload, "mode", ReproductionMode)
    if mode is not None:
        options["mode"] = mode
    assembler = payload.get("assembler")
    if assembler is not None:
        if assembler not in REPRODUCTION_ASSEMBLERS:
            allowed = ", ".join(sorted(REPRODUCTION_ASSEMBLERS))
            raise ValueError(f"invalid reproduction option 'assembler': {assembler!r}; expected one of {allowed}")
        options["assembler"] = assembler
    cpu = payload.get("cpu")
    if cpu is not None:
        if cpu not in REPRODUCTION_CPUS:
            allowed = ", ".join(sorted(REPRODUCTION_CPUS))
            raise ValueError(f"invalid reproduction option 'cpu': {cpu!r}; expected one of {allowed}")
        options["cpu"] = cpu
    backend = payload.get("backend")
    if backend is not None:
        if backend not in REPRODUCTION_BACKENDS:
            allowed = ", ".join(sorted(REPRODUCTION_BACKENDS))
            raise ValueError(f"invalid reproduction option 'backend': {backend!r}; expected one of {allowed}")
        options["backend"] = backend
    include_dirs = payload.get("include_dirs")
    if "include_dirs" in payload:
        if include_dirs == "auto":
            options["include_dirs"] = "auto"
        elif isinstance(include_dirs, list) and all(isinstance(item, str) for item in include_dirs):
            options["include_dirs"] = list(include_dirs)
        else:
            raise ValueError("reproduction option 'include_dirs' must be 'auto' or a list of strings")
    oracle_modes = payload.get("oracle_modes")
    if "oracle_modes" in payload:
        if not isinstance(oracle_modes, list) or not all(isinstance(item, str) for item in oracle_modes):
            raise ValueError("reproduction option 'oracle_modes' must be a list of strings")
        invalid = [item for item in oracle_modes if item not in REPRODUCTION_ORACLE_MODES]
        if invalid:
            allowed = ", ".join(sorted(REPRODUCTION_ORACLE_MODES))
            raise ValueError(f"invalid reproduction option 'oracle_modes': {invalid[0]!r}; expected one of {allowed}")
        options["oracle_modes"] = list(oracle_modes)
    container_policy = _parse_reproduction_enum_field(
        payload, "container_policy", ReproductionContainerPolicy
    )
    if container_policy is not None:
        options["container_policy"] = container_policy
    relocation_policy = _parse_reproduction_enum_field(
        payload, "relocation_policy", ReproductionRelocationPolicy
    )
    if relocation_policy is not None:
        options["relocation_policy"] = relocation_policy
    comparison = _parse_reproduction_enum_field(payload, "comparison", ReproductionComparison)
    if comparison is not None:
        options["comparison"] = comparison
    requested_exactness = _parse_reproduction_enum_field(
        payload, "requested_exactness", ReproductionRequestedExactness
    )
    if requested_exactness is not None:
        options["requested_exactness"] = requested_exactness
        options["requested_exactness_id"] = REPRODUCTION_REQUESTED_EXACTNESS_IDS[requested_exactness]
    if "raw_output" in payload:
        raw_output = payload["raw_output"]
        if raw_output is None or isinstance(raw_output, (str, dict)):
            options["raw_output"] = raw_output
    file_shape_payload = payload.get("file_shape")
    if isinstance(file_shape_payload, dict):
        file_shape = cast(dict[str, object], options["file_shape"])
        relocation_order = _parse_reproduction_enum_field(
            file_shape_payload, "relocation_order", ReproductionFileShapeOrder
        )
        if relocation_order is not None:
            file_shape["relocation_order"] = relocation_order
            if (
                relocation_order is ReproductionFileShapeOrder.ASSEMBLER_DEFAULT
                and "relocation_policy" not in payload
            ):
                options["relocation_policy"] = ReproductionRelocationPolicy.ASSEMBLER_DEFAULT
            elif (
                relocation_order is ReproductionFileShapeOrder.MATCH_ORIGINAL
                and "relocation_policy" not in payload
            ):
                options["relocation_policy"] = ReproductionRelocationPolicy.PRESERVE_ORIGINAL_ENCODING
        relocation_record = _parse_reproduction_enum_field(
            file_shape_payload, "relocation_record", ReproductionRelocationRecord
        )
        if relocation_record is not None:
            file_shape["relocation_record"] = relocation_record
        section_aux_order = _parse_reproduction_enum_field(
            file_shape_payload, "section_aux_order", ReproductionFileShapeOrder
        )
        if section_aux_order is not None:
            file_shape["section_aux_order"] = section_aux_order


def reproduction_policy_for_options(options: dict[str, object]) -> dict[str, object]:
    mode = _require_reproduction_enum_option(options, "mode", ReproductionMode)
    container_policy = _require_reproduction_enum_option(
        options, "container_policy", ReproductionContainerPolicy
    )
    relocation_policy = _require_reproduction_enum_option(
        options, "relocation_policy", ReproductionRelocationPolicy
    )
    comparison = _require_reproduction_enum_option(options, "comparison", ReproductionComparison)
    requested_exactness = _require_reproduction_enum_option(
        options, "requested_exactness", ReproductionRequestedExactness
    )
    requested_exactness_id = REPRODUCTION_REQUESTED_EXACTNESS_IDS[requested_exactness]
    if mode is ReproductionMode.TEMPLATE_PRESERVED:
        container_policy = ReproductionContainerPolicy.PRESERVE_ORIGINAL
        relocation_policy = ReproductionRelocationPolicy.PRESERVE_ORIGINAL_ENCODING
        comparison = ReproductionComparison.FULL_FILE
    elif mode is ReproductionMode.CANONICAL:
        container_policy = ReproductionContainerPolicy.ASSEMBLER_DEFAULT
        relocation_policy = ReproductionRelocationPolicy.ASSEMBLER_DEFAULT
        comparison = ReproductionComparison.FULL_FILE
    elif mode is ReproductionMode.CONTENT:
        comparison = ReproductionComparison.CONTENT
    elif mode is ReproductionMode.SEMANTIC:
        comparison = ReproductionComparison.SEMANTIC
    return {
        "mode": mode,
        "container_policy": container_policy,
        "relocation_policy": relocation_policy,
        "comparison": comparison,
        "requested_exactness": requested_exactness,
        "requested_exactness_id": requested_exactness_id,
    }


def _parse_reproduction_enum_field[ReproductionEnumT: StrEnum](
    payload: dict[str, object],
    field: str,
    enum_type: type[ReproductionEnumT],
) -> ReproductionEnumT | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, str):
        raise TypeError(f"reproduction option {field!r} must be a string")
    try:
        return enum_type(value)
    except ValueError:
        allowed = ", ".join(item.value for item in enum_type)
        raise ValueError(
            f"invalid reproduction option {field!r}: {value!r}; expected one of {allowed}"
        ) from None


def _require_reproduction_enum_option[ReproductionEnumT: StrEnum](
    options: dict[str, object],
    field: str,
    enum_type: type[ReproductionEnumT],
) -> ReproductionEnumT:
    value = options.get(field)
    if isinstance(value, str):
        try:
            return enum_type(value)
        except ValueError:
            pass
    if not isinstance(value, enum_type):
        raise TypeError(f"reproduction option {field!r} must be a {enum_type.__name__}")
    return value


def _require_requested_exactness_id(
    policy: dict[str, object],
    requested_exactness: ReproductionRequestedExactness,
) -> int:
    expected = REPRODUCTION_REQUESTED_EXACTNESS_IDS[requested_exactness]
    value = policy.get("requested_exactness_id")
    if value != expected:
        raise ValueError(
            f"reproduction policy requested_exactness_id must be {expected} for {requested_exactness.value}"
        )
    return expected


def _effective_reproduction_backend(default_backend: str, options: dict[str, object]) -> str:
    backend = options.get("backend")
    return backend if isinstance(backend, str) and backend != "auto" else default_backend


def _effective_reproduction_assembler(default_assembler: str, options: dict[str, object]) -> str:
    assembler = options.get("assembler")
    return assembler if isinstance(assembler, str) and assembler else default_assembler


def _effective_reproduction_cpu(options: dict[str, object]) -> str:
    cpu = options.get("cpu")
    return cpu if isinstance(cpu, str) and cpu in REPRODUCTION_CPUS else "any"


def _json_ready_reproduction_options(options: Mapping[str, object]) -> dict[str, object]:
    def convert(value: object) -> object:
        if isinstance(value, StrEnum):
            return value.value
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    return cast(dict[str, object], convert(dict(options)))


def _best_effort_effective_metadata_hash(target_dir: Path) -> str | None:
    try:
        return cast(str | None, effective_metadata_hash(target_dir))
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
