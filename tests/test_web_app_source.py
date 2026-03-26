from __future__ import annotations

from pathlib import Path


def test_web_app_requires_disk_manifest_data_instead_of_falling_back() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "scripts"
        / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "function requireObject(value, description)" in app_js
    assert "function requireArray(value, description)" in app_js
    assert "Missing indexed file entry for imported target:" in app_js
    assert 'return `${renderInlineBadges([formatTargetTypeLabel(target.target_type)])} Target`;' not in app_js
    assert "const manifest = projectData.disk_manifest || {};" not in app_js
    assert "const analysis = manifest.analysis || {};" not in app_js
    assert "const importedTargets = manifest.imported_targets || [];" not in app_js
    assert "const files = analysis.files || [];" not in app_js


def test_web_app_allows_non_dos_disk_targets_without_indexed_files() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "scripts"
        / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "if (!importedTargets.length) {" in app_js
    assert 'const files = requireArray(analysis.files, "Indexed disk files");' in app_js
    assert 'const hasIndexedFiles = analysis.files !== null && analysis.files !== undefined;' in app_js
    assert '${files ? \'<button class="disk-tab-button" type="button" data-tab="contents" role="tab" aria-selected="false">Disk Contents</button>\' : ""}' in app_js
