from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import source_export
from amiga_reversing.disasm.macos_target_artifact import (
    MACOS_EXAMPLE_PROJECT_ID,
    MACOS_EXAMPLE_SUBTARGET_ID,
)
from amiga_reversing.disasm.source_rendering import SourceRenderingResult
from amiga_reversing.tools import source_export as source_export_cli


def test_source_export_payload_includes_header_and_source(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_source = SimpleNamespace(read_bytes=lambda: b"\x01\x02")
    monkeypatch.setattr(
        source_export,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )
    monkeypatch.setattr(
        source_export,
        "render_source_from_binary_source",
        lambda **kwargs: SourceRenderingResult(
            status="ok",
            source_text="    rts\n",
            listing_profile={"facts_v2": {}},
            workflow_profile={
                "workflow_id": "source_export",
                "target_id": "demo target",
                "spans": [{"name": "source_rendering", "seconds": 0.0, "module": "c_backend"}],
            },
            metadata_hash="metadata-hash",
            target_identity_sha256="identity",
        ),
    )

    payload = source_export.source_export_payload("demo target", assembler_profile="devpac", project_root=tmp_path)

    assert payload["status"] == "ok"
    assert payload["filename"] == "demo-target-devpac.s"
    assert payload["assembler_profile"] == "devpac"
    assert "; Target: demo target" in payload["source_text"]
    assert "; Assembler profile: devpac" in payload["source_text"]
    assert "; Metadata hash: metadata-hash" in payload["source_text"]
    assert "Export is not verification" in payload["source_text"]
    assert "    rts" in payload["source_text"]
    assert payload["target_identity_sha256"]
    workflow_profile = payload["workflow_profile"]
    assert workflow_profile["workflow_id"] == "source_export"
    assert workflow_profile["target_id"] == "demo target"
    assert workflow_profile["spans"][0]["name"] == "source_rendering"
    assert workflow_profile["spans"][0]["module"] == "c_backend"


def test_source_export_rejects_invalid_profile() -> None:
    with pytest.raises(ValueError, match="invalid source export assembler profile"):
        source_export.source_export_payload("demo", assembler_profile="bad")


def test_source_export_returns_refusal_payload(monkeypatch, tmp_path: Path) -> None:
    target_dir = tmp_path / "targets" / "demo"
    target_dir.mkdir(parents=True)
    binary_source = SimpleNamespace(read_bytes=lambda: b"\x01\x02")
    profile = {
        "facts_v2": {
            "asm_source_refused": True,
            "required_instruction_failures": 1,
            "first_required_instruction_failure_section": 0,
            "first_required_instruction_failure_offset": 2,
        }
    }
    monkeypatch.setattr(
        source_export,
        "resolve_project_paths",
        lambda target, project_root: SimpleNamespace(target_dir=target_dir, binary_source=binary_source),
    )
    monkeypatch.setattr(
        source_export,
        "render_source_from_binary_source",
        lambda **kwargs: SourceRenderingResult(
            status="refused",
            source_text="",
            listing_profile=profile,
            workflow_profile={
                "workflow_id": "source_export",
                "target_id": "demo",
                "spans": [{"name": "source_rendering", "seconds": 0.0, "module": "c_backend"}],
            },
            metadata_hash="metadata-hash",
            target_identity_sha256="identity",
            refusal_message="facts_v2 asm source refused required_instruction_failure section=0 offset=2",
        ),
    )

    payload = source_export.source_export_payload("demo", project_root=tmp_path)

    assert payload["status"] == "refused"
    assert "facts_v2 asm source refused" in payload["message"]
    assert payload["listing_profile"] == profile
    assert payload["workflow_profile"]["spans"][0]["name"] == "source_rendering"
    assert "source_text" not in payload


def test_source_export_supports_macos_artifact_renderer(monkeypatch, tmp_path: Path) -> None:
    target_name = f"{MACOS_EXAMPLE_PROJECT_ID}__{MACOS_EXAMPLE_SUBTARGET_ID}"
    target_dir = tmp_path / "targets" / MACOS_EXAMPLE_PROJECT_ID / "targets" / MACOS_EXAMPLE_SUBTARGET_ID
    target_dir.mkdir(parents=True)
    (target_dir / ".project.json").write_text(
        """
{
  "created_at": "2026-05-21T00:00:00+00:00",
  "origin": {
    "artifact": "asm.s",
    "hfs_path": "MPW-GM/MPW/Tools/Asm",
    "kind": "macos_hfs_resource_code_file",
    "renderer": "amiga_reversing.disasm.macos_target_artifact",
    "selected_code_resource_id": 1,
    "source_image": "resources/platform_macos/MPW-GM.img.bin"
  },
  "schema_version": 2,
  "updated_at": "2026-05-21T00:00:00+00:00"
}
""".lstrip(),
        encoding="utf-8",
    )
    monkeypatch.setattr(source_export, "render_macos_example_asm", lambda project_root: "\tINCLUDE \"SegLoad.a\"\n")

    payload = source_export.source_export_payload(target_name, project_root=tmp_path)

    assert payload["status"] == "ok"
    assert payload["target"] == target_name
    assert payload["listing_profile"]["backend"] == "macos-target-artifact"
    assert "; Target: macos_hfs_mpw_gm__macos_file_mpw_tools_asm" in payload["source_text"]
    assert "\tINCLUDE \"SegLoad.a\"" in payload["source_text"]


def test_source_export_cli_writes_file_and_reports_non_verification(monkeypatch, tmp_path: Path, capsys) -> None:
    output = tmp_path / "demo.s"
    monkeypatch.setattr(
        source_export_cli,
        "source_export_payload",
        lambda target, assembler_profile: {
            "status": "ok",
            "filename": "demo-devpac.s",
            "source_text": "; Export is not verification\n",
        },
    )

    assert source_export_cli.main(["demo", "--assembler-profile", "devpac", "--output", str(output)]) == 0

    assert output.read_text(encoding="utf-8") == "; Export is not verification\n"
    assert "not verification" in capsys.readouterr().out


def test_source_export_cli_reports_refusal(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        source_export_cli,
        "source_export_payload",
        lambda target, assembler_profile: {"status": "refused", "message": "no source"},
    )

    assert source_export_cli.main(["demo"]) == 2

    assert "source export refused: no source" in capsys.readouterr().err
