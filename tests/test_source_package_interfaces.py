from __future__ import annotations

import base64
import io
import zipfile
import shutil
import subprocess
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


def test_server_layout_option_is_forwarded_and_refusal_is_not_promoted(monkeypatch):
    monkeypatch.setattr(server,'get_project',lambda _:SimpleNamespace(ready=True))
    monkeypatch.setattr(server,'_is_listing_project',lambda _:True)
    calls=[]
    def export(target,**options):
        calls.append(options)
        return dict(status='refused',reason='unknown_memory_layout',layout_id=options['layout_id'])
    monkeypatch.setattr(server,'source_export_payload',export)
    result=server._source_export_payload('demo',dict(layout_id=['missing'],binary_assets=['true']))
    assert calls[0]['layout_id']=='missing'
    assert result['status']=='refused' and 'archive_base64' not in result


def test_layout_export_palette_action_uses_existing_non_mutating_export():
    from amiga_reversing.disasm.manual_action_catalog import target_action_catalog
    item=next(x for x in target_action_catalog() if x['action_id']=='target.layout_export')
    assert item['action']=='export_source' and item['appends_to_manual_action_log'] is False
    assert item['parameter_schema']['required']==['layout_id','assembler_profile']


def test_ui_layout_export_forwards_selection_and_does_not_download_refusal(tmp_path):
    node=shutil.which('node')
    if node is None:pytest.skip('UI forwarding execution requires Node.js')
    app=(Path(__file__).resolve().parents[1]/'amiga_reversing/web/app.js').read_text()
    function=app[app.index('async function exportSource('):app.index('async function loadSourceArtifact(')]
    script=tmp_path/'layout-export.js'
    script.write_text('''
const assert = require('node:assert/strict');
const state = {project: 'folder/demo'};
const calls = [], statuses = []; let refused = false, downloads = 0;
async function fetchJson(url) { calls.push(url); return refused ? {status:'refused', message:'unknown layout'} : {status:'ok', layout_id:'placed', source_text:'rts', filename:'placed.s'}; }
function showSourceQualityDiagnosticsOverlay() {}
function closeSourceQualityDiagnosticsOverlay() {}
function setAnalysisStatus(text) { statuses.push(text); }
const document = {createElement: () => ({click: () => downloads++, remove: () => {}}), body:{appendChild: () => {}}};
const PreferenceSync = {mergePreferences: () => {}};
async function saveUiPreferenceState() {}
''' + function + '''
(async () => {
 await exportSource('vasm-package','placed');
 assert.match(calls[0], /folder%2Fdemo/); assert.match(calls[0], /binary_assets=true/);
 assert.match(calls[0], /layout_id=placed/); assert.equal(downloads,1);
 assert.match(statuses.at(-1), /qualification is separate/);
 refused = true; await exportSource('vasm-package','missing');
 assert.equal(downloads,1); assert.match(statuses.at(-1), /refused/);
})().catch(error => {console.error(error);process.exitCode=1;});
''')
    subprocess.run([node,str(script)],check=True,capture_output=True,text=True)
