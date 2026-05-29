from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from amiga_reversing.disasm.assembler_profiles import load_assembler_profile
from amiga_reversing.disasm.binary_source import BinarySourceKind
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
) -> dict[str, object]:
    try:
        return render_source_export(
            target_name,
            assembler_profile=assembler_profile,
            project_root=project_root,
        )
    except SourceExportRefused as exc:
        return exc.payload


def render_source_export(
    target_name: str,
    *,
    assembler_profile: str = "vasm",
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    profile = _require_source_export_profile(assembler_profile)
    artifact_payload = _renderer_backed_source_export(
        target_name,
        assembler_profile=profile,
        project_root=project_root,
    )
    if artifact_payload is not None:
        return artifact_payload
    paths = resolve_project_paths(target_name, project_root=project_root)
    renderer = SOURCE_BINARY_RENDERERS.get(paths.binary_source.kind)
    if renderer is None:
        raise ValueError(f"source export does not support binary source kind: {paths.binary_source.kind}")
    return renderer(target_name, paths, profile, project_root)


def _c_backend_binary_source_export(
    target_name: str,
    paths: ProjectPaths,
    assembler_profile: str,
    project_root: Path,
) -> dict[str, object]:
    binary_source = paths.binary_source
    with effective_metadata_file(paths.target_dir) as metadata_path:
        rendering = render_source_from_binary_source(
            target_id=target_name,
            binary_source=binary_source,
            target_dir=paths.target_dir,
            metadata_path=metadata_path,
            project_root=project_root,
            workflow_id="source_export",
        )
    filename = f"{_safe_filename(target_name)}-{assembler_profile}.s"
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
            }
        )
    header = _source_export_header(
        target_name,
        assembler_profile=assembler_profile,
        metadata_hash=rendering.metadata_hash,
        target_identity_sha256=rendering.target_identity_sha256,
    )
    return {
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
