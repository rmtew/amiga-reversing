from __future__ import annotations

import base64
import io
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from amiga_reversing.disasm import server, source_export
from amiga_reversing.disasm.restoration_client import RestorationClient
from amiga_reversing.disasm.source_package import build_source_package
from amiga_reversing.tools import source_export as cli


def exported():
    payload = {"status": "ok", "filename": "demo.s", "source_text": "\trts\n", "target": "demo",
               "assembler_profile": "vasm", "metadata_hash": "metadata", "target_identity_sha256": "binary"}
    return {**payload, "package": build_source_package(payload, [], 256)}


def test_source_export_route_returns_complete_archive(monkeypatch):
    monkeypatch.setattr(server, "get_project", lambda _: SimpleNamespace(ready=True))
    monkeypatch.setattr(server, "_is_listing_project", lambda _: True)
    calls = []
    monkeypatch.setattr(server, "source_export_payload", lambda target, **options: calls.append(options) or exported())
    result = server._source_export_payload("demo", {"binary_assets": ["true"], "minimum_asset_size": ["512"]})
    assert calls[0]["binary_assets"] is True and calls[0]["minimum_asset_size"] == 512
    assert result["archive_filename"] == "demo.zip"
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(result["archive_base64"]))) as archive:
        assert archive.read("demo.s") == b"\trts\n"
        assert archive.comment.decode() == result["package"]["sha256"]


def test_cli_package_regenerates_single_zip(monkeypatch, tmp_path: Path):
    calls = []
    monkeypatch.setattr(cli, "source_export_payload", lambda target, **options: calls.append(options) or exported())
    output = tmp_path / "demo.zip"
    assert cli.main(["demo", "--binary-assets", "--output", str(output)]) == 0
    before = output.read_bytes()
    assert cli.main(["demo", "--binary-assets", "--output", str(output)]) == 0
    assert output.read_bytes() == before
    assert calls[0]["binary_assets"] is True


def test_restoration_adapters_use_existing_source_export_operation(monkeypatch):
    client = RestorationClient()
    calls = []
    def request(path, body=None):
        calls.append((path, body))
        return {"data": {"web_app_contract_version": 2} if path == "/api/app-contract" else exported()}
    monkeypatch.setattr(client, "_request", request)
    result = client.call("folder/demo", "export", binary_assets=True, minimum_asset_size=256)
    assert result["package"] == exported()["package"]
    assert calls[-1] == ("/api/projects/folder%2Fdemo/source-export?binary_assets=true&minimum_asset_size=256", None)


def test_devpac_assets_are_explicitly_unverified():
    with pytest.raises(ValueError, match="Devpac INCBIN alignment is not verified"):
        source_export.source_export_payload("demo", assembler_profile="devpac", binary_assets=True)
