from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amiga_reversing.disasm.binary_source import BinarySource, read_binary_source_bytes
from amiga_reversing.disasm.c_backend import (
    listing_artifact_source_projection_with_c_backend_profile,
)
from amiga_reversing.disasm.effective_metadata import effective_metadata_hash
from amiga_reversing.disasm.facts_v2_source_refusal import (
    FactsV2SourceRefused,
    facts_v2_source_refusal_message,
    facts_v2_source_refused,
)
from amiga_reversing.disasm.workflow_profile import WorkflowProfile


@dataclass(frozen=True, slots=True)
class SourceRenderingResult:
    status: str
    source_text: str
    listing_profile: dict[str, object]
    workflow_profile: dict[str, object]
    metadata_hash: str
    target_identity_sha256: str
    refusal_message: str | None = None
    source_package: dict[str, Any] | None = None
    inline_source_text: str | None = None

    @property
    def refused(self) -> bool:
        return self.status == "refused"


def render_source_from_binary_source(
    *,
    target_id: str,
    binary_source: BinarySource,
    target_dir: Path,
    metadata_path: Path | None,
    project_root: Path,
    workflow_id: str = "source_rendering",
    use_persisted_policy: bool = True,
    artifact=None,
) -> SourceRenderingResult:
    workflow_profile = WorkflowProfile(workflow_id, target_id=target_id)
    render_started_at = time.perf_counter()
    try:
        if artifact is None:
            source_text, listing_profile, native_package = listing_artifact_source_projection_with_c_backend_profile(
                binary_source, metadata_path=metadata_path, project_root=project_root,
                use_persisted_policy=use_persisted_policy)
        else:
            source_text, listing_profile, native_package = artifact.source_projection_with_profile(
                use_persisted_policy=use_persisted_policy)
    except FactsV2SourceRefused as exc:
        source_text = ""
        listing_profile = exc.listing_profile
        native_package = None
    workflow_profile.add_span(
        "source_rendering",
        time.perf_counter() - render_started_at,
        module="c_backend",
        detail={"listing_profile": listing_profile},
    )
    refusal_message = (
        facts_v2_source_refusal_message(listing_profile)
        if facts_v2_source_refused(listing_profile)
        else None
    )
    metadata_hash = effective_metadata_hash(target_dir)
    target_identity = _sha256_bytes(read_binary_source_bytes(binary_source))
    package = None
    inline_source_text = source_text
    if native_package is not None and refusal_message is None:
        inline_source_text = str(native_package["canonical_source_text"])
        package = build_rendered_source_package(
            target_id=target_id, target_dir=target_dir, source_text=source_text,
            listing_profile=listing_profile, metadata_hash=metadata_hash,
            target_identity_sha256=target_identity, project_root=project_root,
            assets=native_package["assets"],
            minimum_asset_size=int(native_package["minimum_asset_size"]))
    return SourceRenderingResult(
        status="refused" if refusal_message is not None else "ok",
        source_text=source_text,
        listing_profile=listing_profile,
        workflow_profile=workflow_profile.to_payload(),
        metadata_hash=metadata_hash,
        target_identity_sha256=target_identity,
        refusal_message=refusal_message,
        source_package=package,
        inline_source_text=inline_source_text,
    )


def render_source_from_binary_source_or_raise(
    *,
    target_id: str,
    binary_source: BinarySource,
    target_dir: Path,
    metadata_path: Path | None,
    project_root: Path,
    workflow_id: str = "source_rendering",
    use_persisted_policy: bool = True,
    artifact=None,
) -> SourceRenderingResult:
    result = render_source_from_binary_source(
        target_id=target_id,
        binary_source=binary_source,
        target_dir=target_dir,
        metadata_path=metadata_path,
        project_root=project_root,
        workflow_id=workflow_id,
        use_persisted_policy=use_persisted_policy,
        artifact=artifact,
    )
    if result.refused:
        raise FactsV2SourceRefused(result.listing_profile)
    return result


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_rendered_source_package(*, target_id: str, target_dir: Path, source_text: str,
    listing_profile: dict[str, object], metadata_hash: str, target_identity_sha256: str,
    project_root: Path, assets: list[dict[str, Any]], minimum_asset_size: int = 256,
    filename: str | None = None) -> dict[str, Any]:
    from amiga_reversing.disasm.source_package import build_source_package, collect_package_includes
    candidates = sorted(target_dir.glob("*.s"))
    if filename is None:
        filename = candidates[0].name if len(candidates) == 1 else "source.s"
    include_root = project_root / "ext" / "amiga_includes" / "ndk_2.0" / "include"
    if listing_profile.get("backend") == "atari-st":
        include_root = project_root / "ext" / "atarist_includes" / "devpac_3_10" / "include"
    return build_source_package({"target": target_id, "filename": filename,
        "source_text": source_text, "assembler_profile": "vasm", "metadata_hash": metadata_hash,
        "target_identity_sha256": target_identity_sha256}, assets, minimum_asset_size,
        includes=collect_package_includes(source_text, include_root))


def publish_rendered_source(rendering: SourceRenderingResult, source_path: Path, *,
                            target_id: str, project_root: Path) -> None:
    """Publish normal source plus only its manifest-owned companions."""
    from amiga_reversing.disasm.source_package_publish import PUBLISH_MANIFEST, publish_source_package
    package = rendering.source_package
    if package is None and not (source_path.parent / PUBLISH_MANIFEST).exists():
        source_path.write_text(rendering.source_text, encoding="utf-8", newline="\n")
        return
    if package is None:
        package = build_rendered_source_package(target_id=target_id, target_dir=source_path.parent,
            source_text=rendering.source_text, listing_profile=rendering.listing_profile,
            metadata_hash=rendering.metadata_hash, target_identity_sha256=rendering.target_identity_sha256,
            project_root=project_root, assets=[], filename=source_path.name)
    if package["manifest"]["source"] != source_path.name:
        raise ValueError("Source package filename differs from canonical output")
    publish_source_package(package, source_path.parent, expected_source_text=rendering.inline_source_text)
