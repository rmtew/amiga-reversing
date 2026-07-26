from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import time
from collections.abc import Mapping
from enum import StrEnum
from pathlib import Path
from typing import cast

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import (
    AssetDataBinarySource,
    BinarySource,
    BinarySourceKind,
    DiskEntryBinarySource,
    HunkFileBinarySource,
    MacosCodeResourceSource,
    RawBinarySource,
    read_binary_source_bytes,
)
from amiga_reversing.disasm.c_backend import (
    reproduction_compare_rebuilt_bytes_with_c_backend_profile,
)
from amiga_reversing.disasm.cli import gen_disasm
from amiga_reversing.disasm.effective_metadata import effective_metadata_file
from amiga_reversing.disasm.project_paths import PROJECT_ROOT, resolve_project_paths
from amiga_reversing.disasm.source_rendering import (
    render_source_from_binary_source_or_raise,
)
from amiga_reversing.disasm.tool_graph import resolve_capability
from amiga_reversing.disasm.workflow_profile import (
    WorkflowProfile,
    workflow_profile_payload,
)

ORACLE_OUTPUT_EXCERPT_CHARS = 4000
ORACLE_TIMEOUT_SECONDS = 120


class OracleComparisonLevel(StrEnum):
    FULL_FILE_MATCH = "oracle.full_file_match"
    CONTENT_MATCH = "oracle.content_match"
    MISMATCH = "oracle.mismatch"
    NOT_COMPARABLE = "oracle.not_comparable"
    MISSING = "oracle.missing"
    NOT_RUN = "oracle.not_run"


ORACLE_COMPARISON_LEVELS = tuple(level.value for level in OracleComparisonLevel)


def oracle_compatibility_reports_for_options(
    target_name: str,
    options: Mapping[str, object],
    *,
    project_root: Path = PROJECT_ROOT,
) -> list[dict[str, object]]:
    oracle_modes = options.get("oracle_modes")
    if not isinstance(oracle_modes, list):
        return []
    reports: list[dict[str, object]] = []
    for mode in dict.fromkeys(item for item in oracle_modes if isinstance(item, str)):
        if mode == "vasm":
            reports.append(run_vasm_oracle(target_name, project_root=project_root))
        elif mode == "devpac":
            reports.append(run_genam_oracle(target_name, project_root=project_root))
    return reports


def run_vasm_oracle(target_name: str, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    capability, workflow_profile = _resolve_capability_with_workflow(
        target_name,
        "assemble_vasm_source",
        project_root=project_root,
    )
    availability = [_availability_record_from_capability(capability)]
    tool_chain = _tool_chain_from_capability(capability, ["vasm"])
    missing = _missing_or_error_report(
        oracle_id="vasm",
        source_profile="vasm",
        tool_chain=tool_chain,
        availability=availability,
    )
    if missing is not None:
        return _with_workflow_profile(missing, workflow_profile)
    vasm_path = _selected_capability_path(capability, "functional_resolved_path")
    if vasm_path is None:
        return _with_workflow_profile(
            _tool_error_report("vasm", "vasm", tool_chain, availability, "capability selected no vasm path"),
            workflow_profile,
        )
    started_at = time.perf_counter()
    paths = resolve_project_paths(target_name, project_root=project_root)
    binary_source = paths.binary_source
    try:
        output_format = _vasm_format_for_source_kind(binary_source.kind)
    except ValueError as exc:
        return _with_workflow_profile(
            _base_report(
                oracle_id="vasm",
                source_profile="vasm",
                tool_chain=tool_chain,
                availability=availability,
                comparison_level=OracleComparisonLevel.NOT_COMPARABLE,
                assembler_status="not_run",
                message=str(exc),
            ),
            workflow_profile,
        )
    temp_root = Path(tempfile.mkdtemp(prefix="oracle_vasm_"))
    invocation_started_at = time.perf_counter()
    try:
        source_path = temp_root / f"{target_name}.s"
        output_path = temp_root / Path(binary_source.display_path).name
        rendered_source, source_profile_payload = _render_vasm_source(
            target_name,
            binary_source,
            paths.target_dir,
            project_root,
        )
        _write_source_text(source_path, rendered_source, "vasm")
        command = [
            vasm_path,
            output_format,
            "-m68000",
            "-no-opt",
            "-quiet",
            "-nosym",
            *_vasm_include_args(project_root),
            "-o",
            str(output_path),
            str(source_path),
        ]
        completed = _run_command(command, cwd=project_root)
        report = _report_from_command(
            oracle_id="vasm",
            source_profile="vasm",
            tool_chain=tool_chain,
            availability=availability,
            binary_source=binary_source,
            output_path=output_path,
            command=command,
            completed=completed,
            source_text=rendered_source,
            source_profile_payload=source_profile_payload,
            elapsed_seconds=time.perf_counter() - started_at,
            project_root=project_root,
            target_dir=paths.target_dir,
        )
    except Exception as exc:
        report = _tool_error_report("vasm", "vasm", tool_chain, availability, str(exc))
    finally:
        workflow_profile.add_span(
            "oracle_invocation",
            time.perf_counter() - invocation_started_at,
            module="oracle_compatibility",
            detail=_oracle_invocation_span_detail(
                capability,
                oracle_id="vasm",
                source_profile="vasm",
                tool_chain=tool_chain,
            ),
        )
        shutil.rmtree(temp_root, ignore_errors=True)
    return _with_workflow_profile(report, workflow_profile)


def run_genam_oracle(target_name: str, *, project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    capability, workflow_profile = _resolve_capability_with_workflow(
        target_name,
        "assemble_devpac_source",
        project_root=project_root,
    )
    availability = [_availability_record_from_capability(capability)]
    tool_chain = _tool_chain_from_capability(capability, ["vamos", "genam"])
    missing = _missing_or_error_report(
        oracle_id="genam-devpac",
        source_profile="devpac",
        tool_chain=tool_chain,
        availability=availability,
    )
    if missing is not None:
        return _with_workflow_profile(missing, workflow_profile)
    vamos_path = _selected_capability_path(capability, "runtime_resolved_path")
    genam_path = _selected_capability_path(capability, "functional_resolved_path")
    if vamos_path is None or genam_path is None:
        return _with_workflow_profile(
            _tool_error_report(
                "genam-devpac",
                "devpac",
                tool_chain,
                availability,
                "capability selected no GenAm runtime chain paths",
            ),
            workflow_profile,
        )
    started_at = time.perf_counter()
    paths = resolve_project_paths(target_name, project_root=project_root)
    binary_source = paths.binary_source
    if isinstance(binary_source, DiskEntryBinarySource | AssetDataBinarySource | MacosCodeResourceSource):
        return _with_workflow_profile(
            _base_report(
                oracle_id="genam-devpac",
                source_profile="devpac",
                tool_chain=tool_chain,
                availability=availability,
                comparison_level=OracleComparisonLevel.NOT_COMPARABLE,
                assembler_status="not_run",
                message=f"GenAm oracle target must be an Amiga file-backed target: {target_name}",
            ),
            workflow_profile,
        )
    temp_root = Path(tempfile.mkdtemp(prefix="oracle_genam_"))
    invocation_started_at = time.perf_counter()
    try:
        source_path = temp_root / f"{Path(binary_source.display_path).stem}.s"
        rendered_source, source_profile_payload = _render_devpac_source(binary_source, source_path, project_root)
        output_name = Path(binary_source.display_path).name
        output_path = temp_root / output_name
        include_arg: list[str] = []
        include_root = load_assembler_profile("devpac").local_include_root
        if include_root is not None:
            include_src = (project_root / include_root).resolve()
            if include_src.is_dir():
                shutil.copytree(include_src, temp_root / "include")
                include_arg = ["INCDIR", "TMP:include/"]
        command = [
            vamos_path,
            "-V",
            f"TMP:{temp_root}",
            "--",
            genam_path,
            f"TMP:{source_path.name}",
            *_devpac_output_args("devpac", output_name),
            "QUIET",
            *include_arg,
        ]
        completed = _run_command(command, cwd=project_root)
        report = _report_from_command(
            oracle_id="genam-devpac",
            source_profile="devpac",
            tool_chain=tool_chain,
            availability=availability,
            binary_source=binary_source,
            output_path=output_path,
            command=command,
            completed=completed,
            source_text=rendered_source,
            source_profile_payload=source_profile_payload,
            elapsed_seconds=time.perf_counter() - started_at,
            project_root=project_root,
            target_dir=paths.target_dir,
        )
    except Exception as exc:
        report = _tool_error_report("genam-devpac", "devpac", tool_chain, availability, str(exc))
    finally:
        workflow_profile.add_span(
            "oracle_invocation",
            time.perf_counter() - invocation_started_at,
            module="oracle_compatibility",
            detail=_oracle_invocation_span_detail(
                capability,
                oracle_id="genam-devpac",
                source_profile="devpac",
                tool_chain=tool_chain,
            ),
        )
        shutil.rmtree(temp_root, ignore_errors=True)
    return _with_workflow_profile(report, workflow_profile)


def _render_vasm_source(
    target_name: str,
    binary_source: BinarySource,
    target_dir: Path,
    project_root: Path,
) -> tuple[str, dict[str, object]]:
    with effective_metadata_file(target_dir) as metadata_path:
        rendering = render_source_from_binary_source_or_raise(
            target_id=target_name,
            binary_source=binary_source,
            target_dir=target_dir,
            metadata_path=metadata_path,
            project_root=project_root,
            workflow_id="oracle_compatibility_source_rendering",
        )
        return rendering.source_text, rendering.listing_profile


def _render_devpac_source(
    binary_source: HunkFileBinarySource | RawBinarySource,
    source_path: Path,
    project_root: Path,
) -> tuple[str, dict[str, object]]:
    binary_path = Path(binary_source.path)
    if not binary_path.is_absolute():
        binary_path = project_root / binary_path
    gen_disasm(str(binary_path), str(source_path), assembler_profile_name="devpac")
    return source_path.read_text(encoding="utf-8"), {}


def _write_source_text(path: Path, text: str, profile_name: str) -> None:
    profile = load_assembler_profile(profile_name)
    newline = "\n" if profile.render.line_ending == "lf" else "\r\n"
    path.write_text(text, encoding="utf-8", newline=newline)


def _devpac_output_args(profile_name: str, out_name: str) -> list[str]:
    profile = load_assembler_profile(profile_name)
    if profile.render.assembler_id != "devpac":
        raise ValueError(f"oracle assembler is not DevPac: {profile_name}")
    if profile.output_file_option == "TO <filename>":
        return ["TO", f"TMP:{out_name}"]
    if profile.output_file_option == "-O<filename>":
        return [f"-OTMP:{out_name}"]
    raise ValueError(f"Unsupported DevPac output_file option: {profile.output_file_option}")


def _report_from_command(
    *,
    oracle_id: str,
    source_profile: str,
    tool_chain: list[str],
    availability: list[dict[str, object]],
    binary_source: BinarySource,
    output_path: Path,
    command: list[str],
    completed: subprocess.CompletedProcess[str],
    source_text: str,
    source_profile_payload: dict[str, object],
    elapsed_seconds: float,
    project_root: Path,
    target_dir: Path,
) -> dict[str, object]:
    report = _base_report(
        oracle_id=oracle_id,
        source_profile=source_profile,
        tool_chain=tool_chain,
        availability=availability,
        comparison_level=OracleComparisonLevel.NOT_RUN,
        assembler_status="accepted" if completed.returncode == 0 else "rejected",
        message="oracle assembler accepted source" if completed.returncode == 0 else "oracle assembler rejected source",
    )
    report.update(
        {
            "command": command,
            "returncode": completed.returncode,
            "stdout_excerpt": _excerpt(completed.stdout),
            "stderr_excerpt": _excerpt(completed.stderr),
            "rendered_source_sha256": _sha256_bytes(source_text.encode("utf-8")),
            "rendered_source_size": len(source_text.encode("utf-8")),
            "source_profile_payload": source_profile_payload,
            "elapsed_seconds": round(elapsed_seconds, 4),
        }
    )
    if completed.returncode != 0:
        return report
    if not output_path.exists():
        report.update(
            {
                "comparison_level": OracleComparisonLevel.NOT_COMPARABLE,
                "message": "oracle assembler produced no output",
                "output_exists": False,
            }
        )
        return report
    output_bytes = output_path.read_bytes()
    original_bytes = read_binary_source_bytes(binary_source)
    comparison = _compare_output(binary_source, original_bytes, output_bytes, target_dir, project_root)
    report.update(
        {
            "comparison_level": comparison["comparison_level"],
            "message": comparison["message"],
            "output_exists": True,
            "output_size": len(output_bytes),
            "output_sha256": _sha256_bytes(output_bytes),
            "original_size": len(original_bytes),
            "original_sha256": _sha256_bytes(original_bytes),
            "first_diff_offset": _first_diff_offset(original_bytes, output_bytes),
            "comparison": comparison["comparison"],
        }
    )
    return report


def _compare_output(
    binary_source: BinarySource,
    original_bytes: bytes,
    output_bytes: bytes,
    target_dir: Path,
    project_root: Path,
) -> dict[str, object]:
    if original_bytes == output_bytes:
        return {
            "comparison_level": OracleComparisonLevel.FULL_FILE_MATCH,
            "message": "oracle output matched original bytes",
            "comparison": {"full_file_exact": True, "content_exact": True},
        }
    try:
        with effective_metadata_file(target_dir) as metadata_path:
            profile = reproduction_compare_rebuilt_bytes_with_c_backend_profile(
                binary_source,
                output_bytes,
                metadata_path=metadata_path,
                project_root=project_root,
            )
    except Exception as exc:
        return {
            "comparison_level": OracleComparisonLevel.MISMATCH,
            "message": f"oracle output differs; content comparison unavailable: {exc}",
            "comparison": {"full_file_exact": False, "content_exact": False},
        }
    exactness_id = _int(profile.get("reproduction_compare_exactness_id"))
    content_exact = exactness_id in {1, 2} or profile.get("reproduction_compare_content_exact") is True
    return {
        "comparison_level": OracleComparisonLevel.CONTENT_MATCH if content_exact else OracleComparisonLevel.MISMATCH,
        "message": "oracle output content matched original" if content_exact else "oracle output differed from original",
        "comparison": {
            "full_file_exact": False,
            "content_exact": content_exact,
            "profile": profile,
        },
    }


def _missing_or_error_report(
    *,
    oracle_id: str,
    source_profile: str,
    tool_chain: list[str],
    availability: list[dict[str, object]],
) -> dict[str, object] | None:
    unavailable = [record for record in availability if record.get("status") != "available"]
    if not unavailable:
        return None
    level = (
        OracleComparisonLevel.NOT_RUN
        if any(record.get("status") == "error" for record in unavailable)
        else OracleComparisonLevel.MISSING
    )
    return _base_report(
        oracle_id=oracle_id,
        source_profile=source_profile,
        tool_chain=tool_chain,
        availability=availability,
        comparison_level=level,
        assembler_status="not_run",
        message="; ".join(str(record.get("message") or record.get("tool_id")) for record in unavailable),
    )


def _tool_error_report(
    oracle_id: str,
    source_profile: str,
    tool_chain: list[str],
    availability: list[dict[str, object]],
    message: str,
) -> dict[str, object]:
    return _base_report(
        oracle_id=oracle_id,
        source_profile=source_profile,
        tool_chain=tool_chain,
        availability=availability,
        comparison_level=OracleComparisonLevel.NOT_RUN,
        assembler_status="tool_error",
        message=message,
    )


def _base_report(
    *,
    oracle_id: str,
    source_profile: str,
    tool_chain: list[str],
    availability: list[dict[str, object]],
    comparison_level: OracleComparisonLevel,
    assembler_status: str,
    message: str,
) -> dict[str, object]:
    return {
        "oracle_id": oracle_id,
        "comparison_level": comparison_level,
        "source_profile": source_profile,
        "tool_chain": tool_chain,
        "availability": availability,
        "assembler_status": assembler_status,
        "message": message,
    }


def _resolve_capability_with_workflow(
    target_name: str,
    capability_id: str,
    *,
    project_root: Path,
) -> tuple[dict[str, object], WorkflowProfile]:
    workflow_profile = WorkflowProfile("oracle_compatibility", target_id=target_name)
    started_at = time.perf_counter()
    capability = resolve_capability(capability_id, project_root=project_root)
    workflow_profile.add_span(
        "tool_capability_resolution",
        time.perf_counter() - started_at,
        module="tool_graph",
        detail=_capability_resolution_span_detail(capability),
    )
    return capability, workflow_profile


def _with_workflow_profile(report: Mapping[str, object], workflow_profile: WorkflowProfile) -> dict[str, object]:
    payload = dict(report)
    payload["workflow_profile"] = workflow_profile_payload(workflow_profile)
    return payload


def _capability_resolution_span_detail(capability: Mapping[str, object]) -> dict[str, object]:
    candidates = capability.get("candidates")
    candidate_summaries = [
        _capability_candidate_summary(candidate)
        for candidate in candidates
        if isinstance(candidate, dict)
    ] if isinstance(candidates, list) else []
    selected = capability.get("selected")
    return {
        "capability_id": capability.get("capability_id"),
        "status": capability.get("status"),
        "available": capability.get("available"),
        "selected": _capability_candidate_summary(selected) if isinstance(selected, dict) else None,
        "candidates": candidate_summaries,
    }


def _oracle_invocation_span_detail(
    capability: Mapping[str, object],
    *,
    oracle_id: str,
    source_profile: str,
    tool_chain: list[str],
) -> dict[str, object]:
    selected = capability.get("selected")
    return {
        "oracle_id": oracle_id,
        "source_profile": source_profile,
        "tool_chain": tool_chain,
        "selected": _capability_candidate_summary(selected) if isinstance(selected, dict) else None,
    }


def _capability_candidate_summary(candidate: Mapping[str, object]) -> dict[str, object]:
    return {
        "capability_id": candidate.get("capability_id"),
        "functional_tool_id": candidate.get("functional_tool_id"),
        "runtime_tool_id": candidate.get("runtime_tool_id"),
        "tool_chain": candidate.get("tool_chain"),
        "runnable_status": candidate.get("runnable_status"),
        "artifact_status": candidate.get("artifact_status"),
        "runtime_status": candidate.get("runtime_status"),
        "missing_runtime_ids": candidate.get("missing_runtime_ids"),
        "probe_evidence": candidate.get("probe_evidence"),
    }


def _availability_record_from_capability(capability: Mapping[str, object]) -> dict[str, object]:
    selected = capability.get("selected")
    if not isinstance(selected, dict):
        return {
            "capability_id": capability.get("capability_id"),
            "tool_id": None,
            "status": "missing",
            "required": True,
            "resolved_path": None,
            "runtime_resolved_path": None,
            "message": "no tool candidate found",
        }
    return {
        "capability_id": capability["capability_id"],
        "tool_id": selected["functional_tool_id"],
        "functional_tool_id": selected["functional_tool_id"],
        "runtime_tool_id": selected["runtime_tool_id"],
        "tool_chain": selected["tool_chain"],
        "status": selected["runnable_status"],
        "runnable_status": selected["runnable_status"],
        "artifact_status": selected["artifact_status"],
        "runtime_status": selected["runtime_status"],
        "missing_runtime_ids": selected["missing_runtime_ids"],
        "required": True,
        "resolved_path": selected["functional_resolved_path"],
        "runtime_resolved_path": selected["runtime_resolved_path"],
        "message": selected["message"],
        "probe_evidence": selected["probe_evidence"],
        "version": cast(Mapping[str, object], selected["probe_evidence"]).get("version_text"),
        "executable_stamp": cast(Mapping[str, object], selected["probe_evidence"]).get("executable_stamp"),
    }


def _tool_chain_from_capability(capability: Mapping[str, object], fallback: list[str]) -> list[str]:
    selected = capability.get("selected")
    if isinstance(selected, dict) and isinstance(selected.get("tool_chain"), list):
        return cast(list[str], selected["tool_chain"])
    return fallback


def _selected_capability_path(capability: Mapping[str, object], key: str) -> str | None:
    selected = capability.get("selected")
    if not isinstance(selected, dict):
        return None
    value = selected.get(key)
    return value if isinstance(value, str) and value else None


def _vasm_format_for_source_kind(source_kind: BinarySourceKind) -> str:
    if source_kind is BinarySourceKind.HUNK_FILE:
        return "-Fhunkexe"
    if source_kind is BinarySourceKind.RAW_BINARY:
        return "-Fbin"
    raise ValueError(f"vasm oracle target must be file-backed, got {source_kind!r}")


def _vasm_include_args(project_root: Path) -> list[str]:
    include_dir = project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    return [f"-I{include_dir}"] if include_dir.is_dir() else []


def _run_command(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=ORACLE_TIMEOUT_SECONDS,
        check=False,
    )


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _first_diff_offset(lhs: bytes, rhs: bytes) -> int | None:
    limit = min(len(lhs), len(rhs))
    for index in range(limit):
        if lhs[index] != rhs[index]:
            return index
    if len(lhs) != len(rhs):
        return limit
    return None


def _excerpt(value: str) -> str:
    return value[:ORACLE_OUTPUT_EXCERPT_CHARS]


def _int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
