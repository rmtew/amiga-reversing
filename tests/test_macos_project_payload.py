from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from amiga_reversing.disasm import macos_project_payload
from amiga_reversing.disasm.projects import ProjectKind, ProjectRecord

IMAGE_PATH = Path("resources/platform_macos/MPW-GM.img.bin")
NDIF2RAW_PATH = Path("ext/tools/ndif2raw/ndif2raw.exe")
SAMPLE_DIR = Path("ext/macos_includes/mpw_gm/Interfaces/AStructMacs")


def test_macos_project_payload_uses_c_summary_and_source_fixture_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_path = tmp_path / "sample.a"
    resource_path = tmp_path / "sample.r"
    build_path = tmp_path / "sample.make"
    image_path = tmp_path / "MPW-GM.img.bin"
    source_path.write_text("\tSEG\t'Main'\nStart\tPROC\n\tENDP\n", encoding="utf-8")
    resource_path.write_text("resource 'WIND' (128) {\n};\n", encoding="utf-8")
    build_path.write_text("Sample  \u00c4\u00c4 Sample.a\n    Link -o {Targ} Sample.a.o\n", encoding="utf-8")
    image_path.write_bytes(b"macbinary")
    calls: dict[str, Any] = {}

    def fake_read_hfs(path: Path) -> bytes:
        calls["image_path"] = path
        return b"hfs"

    def fake_summary(data: bytes, hfs_path: str) -> dict[str, object]:
        calls["summary_args"] = (data, hfs_path)
        return {
            "container_kind": "hfs_resource_code_file",
            "file": {
                "path": "MPW-GM/MPW/Tools/Asm",
                "type": "MPST",
                "creator": "MPS ",
                "cnid": 2310,
                "forks": {
                    "data": {"size": 10, "sha256": "data-hash"},
                    "resource": {"size": 20, "sha256": "resource-hash"},
                },
            },
            "resource_fork": {
                "types": [{"type": "CODE", "count": 2}],
                "code_resources": [{"type": "CODE", "id": 1, "size": 6}],
            },
            "selected_code": {
                "available": True,
                "id": 1,
                "payload_size": 6,
                "code_bytes_size": 2,
                "payload_sha256": "payload-hash",
                "code_bytes_sha256": "code-hash",
            },
            "unsupported": ["segment_loader_relocations"],
        }

    monkeypatch.setattr(macos_project_payload, "read_macos_hfs_image_bytes", fake_read_hfs)
    monkeypatch.setattr(macos_project_payload, "inspect_macos_hfs_code_summary_with_c_backend", fake_summary)
    project = ProjectRecord(
        id="macos_mpw_sample",
        name="macos_mpw_sample",
        kind=ProjectKind.MACOS,
        target_dir=str(tmp_path / "targets" / "macos_mpw_sample"),
        output_path=None,
        binary_path=str(image_path),
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=str(image_path),
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_resource_code_file",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
        origin={
            "kind": "macos_mpw_fixture",
            "source_image": image_path.name,
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "source_files": [source_path.name],
            "resource_files": [resource_path.name],
            "build_files": [build_path.name],
        },
    )

    payload = macos_project_payload.build_macos_project_payload(project, project_root=tmp_path)
    container = payload["binary_container_view"]

    assert payload["platform"] == "macos"
    assert calls["image_path"] == image_path
    assert calls["summary_args"] == (b"hfs", "MPW-GM/MPW/Tools/Asm")
    assert container["kind"] == "hfs_resource_code_file"
    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert container["selected_code_segment"]["listing"] == {
        "project_id": "macos_mpw_sample",
        "route": "listing",
        "source_range": {"section_index": 0, "start_offset": 0, "size": 2},
        "resource_type": "CODE",
        "resource_id": 1,
        "resource_name": None,
        "fork": "resource",
        "payload_size": 6,
        "payload_sha256": "payload-hash",
        "code_bytes_sha256": "code-hash",
        "unsupported": ["segment_loader_relocations"],
    }
    assert payload["source_binary_boundary"]["observed_code_fixture"] == "MPW-GM/MPW/Tools/Asm"
    assert payload["provenance"]["binary_container_source"] == "platform_file_lib.macos_hfs_code_summary"


def test_macos_project_payload_reads_committed_mpw_fixture_when_available() -> None:
    if not IMAGE_PATH.exists():
        pytest.skip("MPW-GM image fixture is not available")
    if not NDIF2RAW_PATH.exists():
        pytest.skip("ndif2raw provider is not available")
    required = [SAMPLE_DIR / "Sample.a", SAMPLE_DIR / "Sample.r", SAMPLE_DIR / "Sample.make"]
    if any(not path.exists() for path in required):
        pytest.skip("MPW-GM source fixture metadata is not available")
    project = ProjectRecord(
        id="macos_mpw_sample",
        name="macos_mpw_sample",
        kind=ProjectKind.MACOS,
        target_dir="targets/macos_mpw_sample",
        output_path=None,
        binary_path=IMAGE_PATH.as_posix(),
        ready=True,
        last_opened=None,
        manifest_path=None,
        target_count=None,
        source_path=IMAGE_PATH.as_posix(),
        disk_type="HFS",
        parent_project_id=None,
        target_type="macos_hfs_resource_code_file",
        created_at="2026-03-25T00:00:00+00:00",
        updated_at="2026-03-25T01:00:00+00:00",
        origin={
            "kind": "macos_mpw_fixture",
            "source_image": IMAGE_PATH.as_posix(),
            "hfs_path": "MPW-GM/MPW/Tools/Asm",
            "source_files": [(SAMPLE_DIR / "Sample.a").as_posix()],
            "resource_files": [(SAMPLE_DIR / "Sample.r").as_posix()],
            "build_files": [(SAMPLE_DIR / "Sample.make").as_posix()],
        },
    )

    payload = macos_project_payload.build_macos_project_payload(project)
    container = payload["binary_container_view"]

    assert payload["platform"] == "macos"
    assert container["finder"] == {"type": "MPST", "creator": "MPS ", "cnid": 2310}
    assert len(container["code_resources"]) == 28
    assert container["selected_code_segment"]["code_bytes_size"] == 29020
    assert payload["provenance"]["source_image"] == IMAGE_PATH.as_posix()
