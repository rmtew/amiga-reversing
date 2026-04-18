from __future__ import annotations

from pathlib import Path


def test_web_app_requires_disk_manifest_data_instead_of_falling_back() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
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
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "if (!importedTargets.length) {" in app_js
    assert 'const files = analysis.files === null || analysis.files === undefined' in app_js
    assert ': requireArray(analysis.files, "Indexed disk files");' in app_js
    assert 'String(target.entry_path || "").startsWith("bootloader/")' in app_js
    assert 'const hasIndexedFiles = analysis.files !== null && analysis.files !== undefined;' in app_js
    assert '${files ? \'<button class="disk-tab-button" type="button" data-tab="contents" role="tab" aria-selected="false">Disk Contents</button>\' : ""}' in app_js


def test_web_app_annotation_button_is_hover_only_and_has_fallback_entity() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "let entity;" in app_js
    assert "catch (err)" in app_js
    assert "fallbackEntity" in app_js
    assert ".listing-annotation-edit {\n  opacity: 0;" in styles_css
    assert ".listing-row:hover .listing-annotation-edit" in styles_css
    assert ".listing-row:focus-within .listing-annotation-edit" in styles_css


def test_web_app_initial_listing_load_requests_all_ready_rows() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "await loadListingWindow(projectId, null, 0, Number(jobState.total_rows || 240));" in app_js
    assert "await loadListingWindow(projectId, null, 0, 240);" not in app_js
