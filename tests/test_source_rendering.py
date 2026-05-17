from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from amiga_reversing.disasm import source_rendering


def test_source_rendering_result_owns_profile_and_refusal(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    profile = {
        "facts_v2": {
            "asm_source_refused": True,
            "required_instruction_failures": 1,
            "first_required_instruction_failure_section": 0,
            "first_required_instruction_failure_offset": 2,
        }
    }
    monkeypatch.setattr(
        source_rendering,
        "listing_artifact_source_text_with_c_backend_profile",
        lambda *args, **kwargs: ("", profile),
    )
    monkeypatch.setattr(source_rendering, "effective_metadata_hash", lambda target_dir: "metadata-hash")

    result = source_rendering.render_source_from_binary_source(
        target_id="demo",
        binary_source=SimpleNamespace(read_bytes=lambda: b"\x01\x02"),
        target_dir=target_dir,
        metadata_path=tmp_path / "metadata.json",
        project_root=tmp_path,
    )

    assert result.status == "refused"
    assert "facts_v2 asm source refused" in str(result.refusal_message)
    assert result.listing_profile == profile
    assert result.metadata_hash == "metadata-hash"
    assert result.target_identity_sha256
    assert result.workflow_profile["spans"][0]["name"] == "source_rendering"
