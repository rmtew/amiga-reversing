from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path

from amiga_reversing.disasm.binary_source import BinarySource, read_binary_source_bytes
from amiga_reversing.disasm.c_backend import (
    listing_artifact_source_text_with_c_backend_profile,
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
) -> SourceRenderingResult:
    workflow_profile = WorkflowProfile(workflow_id, target_id=target_id)
    render_started_at = time.perf_counter()
    try:
        source_text, listing_profile = listing_artifact_source_text_with_c_backend_profile(
            binary_source,
            metadata_path=metadata_path,
            project_root=project_root,
        )
    except FactsV2SourceRefused as exc:
        source_text = ""
        listing_profile = exc.listing_profile
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
    return SourceRenderingResult(
        status="refused" if refusal_message is not None else "ok",
        source_text=source_text,
        listing_profile=listing_profile,
        workflow_profile=workflow_profile.to_payload(),
        metadata_hash=effective_metadata_hash(target_dir),
        target_identity_sha256=_sha256_bytes(read_binary_source_bytes(binary_source)),
        refusal_message=refusal_message,
    )


def render_source_from_binary_source_or_raise(
    *,
    target_id: str,
    binary_source: BinarySource,
    target_dir: Path,
    metadata_path: Path | None,
    project_root: Path,
    workflow_id: str = "source_rendering",
) -> SourceRenderingResult:
    result = render_source_from_binary_source(
        target_id=target_id,
        binary_source=binary_source,
        target_dir=target_dir,
        metadata_path=metadata_path,
        project_root=project_root,
        workflow_id=workflow_id,
    )
    if result.refused:
        raise FactsV2SourceRefused(result.listing_profile)
    return result


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
