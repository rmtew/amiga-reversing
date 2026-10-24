from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any, TypedDict

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import BinarySourceKind
from amiga_reversing.disasm.c_backend import (
    build_listing_artifact_profile_from_binary_source,
    listing_artifact_source_package_with_c_backend,
    source_quality_explain_project_source_with_c_backend,
)
from amiga_reversing.disasm.effective_metadata import (
    effective_metadata_file,
)
from amiga_reversing.disasm.macos_target_artifact import (
    MACOS_EXAMPLE_SUBTARGET_ID,
    render_macos_example_asm,
)
from amiga_reversing.disasm.project_paths import (
    PROJECT_ROOT,
    ProjectPaths,
    resolve_project_dir,
    resolve_project_paths,
)
from amiga_reversing.disasm.source_rendering import render_source_from_binary_source
from amiga_reversing.disasm.behaviour_validation import LoadedSource, BehaviourError
from amiga_reversing.disasm import layout_export_cache
from amiga_reversing.disasm.target_history import target_lock

LOADED_SOURCE=LoadedSource(__file__)

SOURCE_EXPORT_ASSEMBLER_PROFILES = ("vasm", "devpac")


class SourceArtifactRendering(TypedDict):
    source_text: str
    listing_profile: dict[str, object]
    workflow_span_name: str
    workflow_span_module: str
    identity_components: list[str]


SourceArtifactRenderer = Callable[[str, Path, dict[str, object], Path], SourceArtifactRendering | None]
BinarySourceExportRenderer = Callable[[str, ProjectPaths, str, Path], dict[str, object]]


class SourceExportRefused(RuntimeError):
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        super().__init__(str(payload.get("message") or "source export refused"))


def source_export_payload(
    target_name: str,
    *,
    assembler_profile: str = "vasm",
    project_root: Path = PROJECT_ROOT,
    binary_assets: bool = False,
    minimum_asset_size: int = 256,
    structure_macros: bool = False,
    layout_id: str | None = None,
) -> dict[str, object]:
    try:
        if layout_id is not None:
            layout_export_cache.implementation_identities(LOADED_SOURCE)
        result = render_source_export(
            target_name,
            assembler_profile=assembler_profile,
            project_root=project_root,
            binary_assets=binary_assets,
            minimum_asset_size=minimum_asset_size,
            structure_macros=structure_macros,
            layout_id=layout_id,
        )
        if layout_id is not None:
            layout_export_cache.implementation_identities(LOADED_SOURCE)
        return result
    except SourceExportRefused as exc:
        return exc.payload
    except layout_export_cache.LayoutExportRefused as exc:
        return exc.payload
    except BehaviourError as exc:
        return dict(status='refused',reason='stale',message=str(exc),restart_required=True)


def render_source_export(
    target_name: str,
    *,
    assembler_profile: str = "vasm",
    project_root: Path = PROJECT_ROOT,
    binary_assets: bool = False,
    minimum_asset_size: int = 256,
    structure_macros: bool = False,
    layout_id: str | None = None,
) -> dict[str, object]:
    if type(binary_assets) is not bool:
        raise ValueError("binary_assets must be boolean")
    if type(structure_macros) is not bool:
        raise ValueError("structure_macros must be boolean")
    if type(minimum_asset_size) is not int or not 1 <= minimum_asset_size <= 0xFFFFFFFF:
        raise ValueError("minimum_asset_size must be 1..4294967295")
    profile = _require_source_export_profile(assembler_profile)
    if layout_id is not None and profile != "vasm":
        raise ValueError("Selected memory layouts currently require vasm")
    if structure_macros and profile != "vasm":
        raise ValueError("Structure macro exports currently require the verified vasm profile")
    if binary_assets and profile != "vasm":
        raise ValueError("Binary-asset packages currently require vasm; native Devpac INCBIN alignment is not verified")
    artifact_payload = _renderer_backed_source_export(
        target_name,
        assembler_profile=profile,
        project_root=project_root,
    )
    if artifact_payload is not None:
        if binary_assets or structure_macros or layout_id is not None:
            raise ValueError("Optional binary-asset or structure-macro projections require a native analysis render plan")
        return artifact_payload
    paths = resolve_project_paths(target_name, project_root=project_root)
    renderer = SOURCE_BINARY_RENDERERS.get(paths.binary_source.kind)
    if renderer is None:
        raise ValueError(f"source export does not support binary source kind: {paths.binary_source.kind}")
    if binary_assets or structure_macros or layout_id is not None:
        if renderer is not _c_backend_binary_source_export:
            raise ValueError("Optional binary-asset or structure-macro projections require the native renderer")
        return _c_backend_binary_source_export(target_name, paths, profile, project_root,
            minimum_asset_size=minimum_asset_size if binary_assets else None, structure_macros=structure_macros,
            layout_id=layout_id)
    return renderer(target_name, paths, profile, project_root)


def _c_backend_binary_source_export(
    target_name: str,
    paths: ProjectPaths,
    assembler_profile: str,
    project_root: Path,
    *, minimum_asset_size: int | None = None,
    structure_macros: bool = False,
    layout_id: str | None = None,
) -> dict[str, object]:
    with target_lock(paths.target_dir):
        return _native_source_export(target_name,paths,assembler_profile,project_root,
            minimum_asset_size=minimum_asset_size,structure_macros=structure_macros,layout_id=layout_id)


def _native_source_export(target_name,paths,assembler_profile,project_root,*,minimum_asset_size=None,
                          structure_macros=False,layout_id=None):
    binary_source = paths.binary_source
    from . import hosted_application_export
    application_contract=None
    with effective_metadata_file(paths.target_dir, **({"layout_id": layout_id} if layout_id is not None else {})) as metadata_path:
        hosted=hosted_application_export.required(metadata_path,layout_id)
        if hosted and minimum_asset_size is None:
            raise SourceExportRefused(dict(status='refused',reason='hosted_application_requires_package',
                message='This hosted profile requires the complete binary-asset source package, including its DOS runtime.'))
        def build():
            return build_listing_artifact_profile_from_binary_source(
                binary_source, metadata_path=metadata_path, project_root=project_root)[2]
        lease=(layout_export_cache.acquire(paths,project_root,metadata_path,build,LOADED_SOURCE,
                   minimum_asset_size if minimum_asset_size is not None else 0xFFFFFFFF,require_native_baseline=hosted)
               if layout_id is not None and metadata_path is not None and not structure_macros else closing(build()))
        with lease as artifact:
            selected_plan = None
            if layout_id is not None:
                selected_plan = next((p for p in artifact.memory_layouts_payload()["items"]
                                      if p["layout_id"] == layout_id), None)
                if selected_plan is None or selected_plan["status"] != "placement_valid":
                    raise ValueError("Selected native memory layout has unresolved placement constraints")
            if hosted:
                application_contract=hosted_application_export.native_contract(artifact,target_name,layout_id)
            rendering = render_source_from_binary_source(
                target_id=target_name,
                binary_source=binary_source,
                target_dir=paths.target_dir,
                metadata_path=metadata_path,
                project_root=project_root,
                workflow_id="source_export",
                use_persisted_policy=False,
                artifact=artifact,
            )
            native_package = None
            if (minimum_asset_size is not None or structure_macros) and not rendering.refused:
                native_package = listing_artifact_source_package_with_c_backend(
                    binary_source, minimum_asset_size=minimum_asset_size if minimum_asset_size is not None else 0xFFFFFFFF,
                    metadata_path=metadata_path, project_root=project_root,
                    structure_macros=structure_macros, artifact=artifact,
                )
                if native_package.pop("canonical_source_text") != rendering.source_text:
                    raise ValueError("Source changed during package export; retry from current state")
        if rendering.refused:
            source_quality_explanation = source_quality_explain_project_source_with_c_backend(
                binary_source, metadata_path=metadata_path, project_root=project_root)
    filename = f"{_safe_filename(target_name)}-{assembler_profile}.s"
    if minimum_asset_size is not None:
        filename = f"{_safe_filename(target_name.encode("ascii", "ignore").decode())}-{assembler_profile}.s"
    if rendering.refused:
        raise SourceExportRefused(
            {
                "status": "refused",
                "target": target_name,
                "assembler_profile": assembler_profile,
                "filename": filename,
                "message": rendering.refusal_message,
                "listing_profile": rendering.listing_profile,
                "workflow_profile": rendering.workflow_profile,
                "metadata_hash": rendering.metadata_hash,
                "target_identity_sha256": rendering.target_identity_sha256,
                "source_quality_explanation": source_quality_explanation,
            }
        )
    header = _source_export_header(
        target_name,
        assembler_profile=assembler_profile,
        metadata_hash=rendering.metadata_hash,
        target_identity_sha256=rendering.target_identity_sha256,
    )
    layout_plan_sha256 = None
    if selected_plan is not None:
        layout_plan_sha256 = hashlib.sha256(json.dumps(selected_plan, sort_keys=True,
            separators=(",", ":")).encode()).hexdigest()
        header += f"; Layout: {layout_id} (source only; runtime unqualified)\n; Layout plan SHA256: {layout_plan_sha256}\n"
    payload: dict[str, object] = {
        "status": "ok",
        "target": target_name,
        "assembler_profile": assembler_profile,
        "filename": filename,
        "source_text": _join_header_and_source(header, rendering.source_text, assembler_profile=assembler_profile),
        "header": header,
        "metadata_hash": rendering.metadata_hash,
        "target_identity_sha256": rendering.target_identity_sha256,
        "listing_profile": rendering.listing_profile,
        "workflow_profile": rendering.workflow_profile,
        "non_verification": True,
    }
    if layout_id is not None:
        payload["layout_id"] = layout_id
        payload["layout_plan_sha256"] = layout_plan_sha256
        payload["layout_plan"] = selected_plan
        payload["layout_status"] = "source_only_unqualified"
        payload["layout_runtime_qualified"] = False

    if native_package is not None:
        from amiga_reversing.disasm.source_package import (
            build_source_package,
            collect_package_includes,
        )
        payload["source_text"] = _join_header_and_source(header, str(native_package["source_text"]),
            assembler_profile=assembler_profile)
        if structure_macros:
            payload["structure_macros"] = native_package["structure_macros"]
        include_root = project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
        if rendering.listing_profile.get("backend") == "atari-st":
            include_root = project_root / "ext" / "atarist_includes" / "devpac_3_10" / "include"
        if minimum_asset_size is not None:
            includes = collect_package_includes(str(payload["source_text"]), include_root)
            payload["package"] = build_source_package(payload, native_package["assets"], minimum_asset_size,
                includes=includes)
    if application_contract is not None:
        payload=hosted_application_export.attach(payload,application_contract,project_root)
    return payload


def _renderer_backed_source_export(
    target_name: str,
    *,
    assembler_profile: str,
    project_root: Path,
) -> dict[str, object] | None:
    try:
        target_dir = resolve_project_dir(target_name, project_root=project_root)
    except FileNotFoundError:
        return None
    metadata_path = target_dir / ".project.json"
    if not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        return None
    origin = metadata.get("origin")
    if not isinstance(origin, dict):
        return None
    renderer_id = origin.get("renderer")
    if not isinstance(renderer_id, str):
        return None
    renderer = SOURCE_ARTIFACT_RENDERERS.get(renderer_id)
    if renderer is None:
        return None
    rendering = renderer(target_name, target_dir, origin, project_root)
    if rendering is None:
        return None
    return _source_artifact_payload(
        target_name,
        target_dir=target_dir,
        metadata_path=metadata_path,
        origin=origin,
        renderer_id=renderer_id,
        rendering=rendering,
        assembler_profile=assembler_profile,
    )


def _source_artifact_payload(
    target_name: str,
    *,
    target_dir: Path,
    metadata_path: Path,
    origin: dict[str, object],
    renderer_id: str,
    rendering: SourceArtifactRendering,
    assembler_profile: str,
) -> dict[str, object]:
    metadata_hash = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
    identity_components = [
        target_name,
        renderer_id,
        str(origin.get("artifact") or ""),
        *rendering["identity_components"],
    ]
    identity_text = "\n".join(identity_components)
    target_identity_sha256 = hashlib.sha256(identity_text.encode("utf-8")).hexdigest()
    header = _source_export_header(
        target_name,
        assembler_profile=assembler_profile,
        metadata_hash=metadata_hash,
        target_identity_sha256=target_identity_sha256,
    )
    return {
        "status": "ok",
        "target": target_name,
        "assembler_profile": assembler_profile,
        "filename": f"{_safe_filename(target_name)}-{assembler_profile}.s",
        "source_text": _join_header_and_source(header, rendering["source_text"], assembler_profile=assembler_profile),
        "header": header,
        "metadata_hash": metadata_hash,
        "target_identity_sha256": target_identity_sha256,
        "listing_profile": rendering["listing_profile"],
        "workflow_profile": {
            "workflow_id": "source_export",
            "target_id": target_name,
            "spans": [
                {
                    "name": rendering["workflow_span_name"],
                    "seconds": 0.0,
                    "module": rendering["workflow_span_module"],
                }
            ],
        },
        "non_verification": True,
    }


def _render_macos_target_artifact_source(
    target_name: str,
    target_dir: Path,
    origin: dict[str, object],
    project_root: Path,
) -> SourceArtifactRendering | None:
    if origin.get("kind") != "macos_hfs_resource_code_file":
        return None
    if origin.get("artifact") != "asm.s":
        return None
    if target_name.split("__")[-1] != MACOS_EXAMPLE_SUBTARGET_ID:
        return None
    return {
        "source_text": render_macos_example_asm(project_root=project_root),
        "listing_profile": {
            "backend": "macos-target-artifact",
            "source_kind": "macos_hfs_resource_code_file",
            "path": str(target_dir),
        },
        "workflow_span_name": "macos_target_artifact_rendering",
        "workflow_span_module": "python",
        "identity_components": [
            str(origin.get("source_image") or ""),
            str(origin.get("hfs_path") or ""),
            str(origin.get("selected_code_resource_id") or ""),
        ],
    }


SOURCE_ARTIFACT_RENDERERS: dict[str, SourceArtifactRenderer] = {
    "amiga_reversing.disasm.macos_target_artifact": _render_macos_target_artifact_source,
}


SOURCE_BINARY_RENDERERS: dict[BinarySourceKind, BinarySourceExportRenderer] = {
    BinarySourceKind.HUNK_FILE: _c_backend_binary_source_export,
    BinarySourceKind.DISK_ENTRY: _c_backend_binary_source_export,
    BinarySourceKind.RAW_BINARY: _c_backend_binary_source_export,
    BinarySourceKind.MACOS_CODE_RESOURCE: _c_backend_binary_source_export,
}


def _require_source_export_profile(assembler_profile: str) -> str:
    if assembler_profile not in SOURCE_EXPORT_ASSEMBLER_PROFILES:
        allowed = ", ".join(SOURCE_EXPORT_ASSEMBLER_PROFILES)
        raise ValueError(f"invalid source export assembler profile {assembler_profile!r}; expected one of {allowed}")
    load_assembler_profile(assembler_profile)
    return assembler_profile


def _source_export_header(
    target_name: str,
    *,
    assembler_profile: str,
    metadata_hash: str,
    target_identity_sha256: str,
) -> str:
    lines = [
        "; Generated by amiga-reversing source export",
        f"; Target: {target_name}",
        f"; Assembler profile: {assembler_profile}",
        f"; Metadata hash: {metadata_hash}",
        f"; Target identity sha256: {target_identity_sha256}",
        "; Export is not verification; run reproduction or oracle checks separately.",
    ]
    return "\n".join(lines) + "\n"


def _join_header_and_source(header: str, source_text: str, *, assembler_profile: str) -> str:
    profile = load_assembler_profile(assembler_profile)
    newline = "\n" if profile.render.line_ending == "lf" else "\r\n"
    text = header + "\n" + source_text.lstrip("\r\n")
    return text.replace("\r\n", "\n").replace("\n", newline)


def _safe_filename(target_name: str) -> str:
    clean = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in target_name)
    return clean.strip("-") or "source-export"


def verify_source_export_package(target_name: str, payload: dict[str, Any], *, project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Use the existing reproduction and oracle pipelines on the identical package."""
    if payload['package']['manifest'].get('application') is not None:
        from .hosted_application_export import verify
        return verify(target_name, payload, project_root)
    from amiga_reversing.disasm.oracle_compatibility import run_vasm_oracle
    from amiga_reversing.disasm.reproduction import run_reproduction
    package = payload["package"]
    report = run_reproduction(target_name, assembler="our", persist_report=False,
        project_root=project_root, pre_rendered_source_text=payload["source_text"],
        pre_rendered_source_profile=payload["listing_profile"], pre_rendered_source_package=package)
    oracle = run_vasm_oracle(target_name, project_root=project_root,
        pre_rendered_source_text=payload["source_text"], pre_rendered_source_profile=payload["listing_profile"],
        pre_rendered_source_package=package)
    return {"package_sha256": package["sha256"],
        "exact": (report.get("comparison") or {}).get("full_file_exact") is True
            and oracle.get("comparison_level") == "oracle.full_file_match",
        "framework": report, "oracle": oracle}
