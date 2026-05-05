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


def test_web_app_initial_listing_load_requests_virtual_window() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "const count = viewport ? listingFetchCount(viewport) : LISTING_INITIAL_ROW_WINDOW;" in app_js
    assert "return loadListingWindow(projectId, null, 0, count, {start: 0, count});" in app_js
    assert "await loadListingWindow(projectId, null, 0, 240);" not in app_js


def test_web_app_generation_refresh_restores_only_applied_request() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "const requestSeqBeforeRefresh = state.virtualListing.requestSeq;" in app_js
    assert "if (state.virtualListing.requestSeq !== requestSeqBeforeRefresh + 1) {" in app_js
    assert "restoreListingAddressAnchor(document.getElementById(\"listing-viewport\"), anchor);" in app_js


def test_web_app_generation_refresh_anchors_non_address_rows() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert 'viewport.querySelectorAll(".listing-row")' in app_js
    assert "stableKey: best.dataset.rowStableKey || null" in app_js
    assert "rowCode: best.dataset.rowCode || \"\"" in app_js
    assert "const shouldUseCodeAnchor = anchor?.rowCode && (isAtListingTop || !Number.isFinite(anchor.addr));" in app_js
    assert "anchorCode: anchor.rowCode" in app_js
    assert 'params.set("anchor_code", String(options.anchorCode).trim());' in app_js
    assert "function selectListingAnchorRow(viewport, anchor)" in app_js
    assert "function listingAnchorRowIndex(anchor)" in app_js
    assert "function listingAnchorScrollTop(listing, anchor)" in app_js
    assert "options.restoreAnchor ? listingAnchorScrollTop(listing, options.restoreAnchor) : null" in app_js
    assert "viewport.scrollTop = Math.max(0, ((state.virtualListing.start + rowIndex) * rowHeight) - anchor.topDelta);" in app_js


def test_web_app_shows_non_occluding_analysis_status() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert 'id="analysis-status" aria-live="polite"' in app_js
    assert "function updateAnalysisStatusFromJob(job)" in app_js
    assert "async function openListingJob(projectId, generation = \"basic\")" in app_js
    assert "body: JSON.stringify({generation})" in app_js
    assert 'id="run-full-analysis"' in app_js
    assert 'const job = await openListingJob(projectId, "basic");' in app_js
    assert 'const job = await openListingJob(projectId, "full");' in app_js
    assert 'setAnalysisStatus("Applying full analysis", "running")' in app_js
    assert 'setAnalysisStatus("Initial listing ready", "ready", 2000)' in app_js
    assert 'setAnalysisStatus("Full analysis ready", "ready", 2000)' in app_js
    assert ".analysis-status" in styles_css
    assert ".listing-viewport .analysis-status" not in styles_css


def test_web_app_exposes_reproduction_badge_panel_and_issue_navigation() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "function reproductionBadge(ready, report)" in app_js
    assert 'id="open-repro"' in app_js
    assert "function renderReproPanel()" in app_js
    assert "function currentReproIssue()" in app_js
    assert "function reproductionReportKey(report)" in app_js
    assert "const previousReportKey = state.reproduction.reportKey || reproductionReportKey(state.reproduction.report);" in app_js
    assert "state.reproduction.reportKey = null;" in app_js
    assert "state.reproduction.reportKey = reproductionReportKey(state.reproduction.report);" in app_js
    assert "state.reproduction.selectedIssueEntry = entry;" in app_js
    assert '`/api/projects/${encodeURIComponent(projectId)}/reproduction/run`' in app_js
    assert '`/api/projects/${encodeURIComponent(state.project)}/target-edits`' in app_js
    assert "payload.hunk = hunk;" in app_js
    assert 'data-repro-edit-kind="label"' in app_js
    assert 'data-repro-edit-kind="external_symbol"' in app_js
    assert "defaultReproSymbolName(issue, kind, addr)" in app_js
    assert 'data-repro-edit-kind="suppress_inferred_pointer"' in app_js
    assert 'return {label: "Unsupported"' in app_js
    assert '"repro-issues": []' in app_js
    assert '["repro-issues", "Repro Issues"]' in app_js
    assert "listing-row-repro-issue" in app_js
    assert ".repro-panel" in styles_css
    assert ".project-badge-repro-exact" in styles_css


def test_web_app_marks_typed_app_slot_refs_without_source_changes() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "function appSlotTypedInfoForSymbol(symbol)" in app_js
    assert "function appSlotFieldPath(field, structName)" in app_js
    assert "function appSlotTypedInfoTitle(info)" in app_js
    assert "listing-app-slot-reference${typedClass}" in app_js
    assert '["app-slot-field-gaps", "App Field Gaps"]' in app_js
    assert "app_slot_field_path:" in app_js
    assert "app_slot_region_source:" in app_js
    assert '["app-slot-suggestions", "App Suggestions"]' in app_js
    assert '["app-slot-api-args", "App API Args"]' in app_js
    assert '["typed-gaps", "Typed Gaps"]' in app_js
    assert "function renderUnresolvedTypedAccessBadges(row)" in app_js
    assert "row.unresolved_typed_accesses" in app_js
    assert "typed_base_unresolved_field" in app_js
    assert "platform_unresolved_typed_access:" in app_js
    assert "platform_prefix_extension_candidate:" in app_js
    assert "refinement_applied" in app_js
    assert "refined_struct_name" in app_js
    assert "function typedGapSummary(access)" in app_js
    assert "function typedGapProvenanceSummary(access)" in app_js
    assert "type_provenance_kind" in app_js
    assert ".project-badge-typed-gap" in styles_css
    assert "untyped_api_arg_count" in app_js
    assert "base_symbol" in app_js
    assert "field_expr" in app_js
    assert "suggestion_count" in app_js
    assert "function navigationEntryHasJumpTarget(entry)" in app_js
    assert "entry.navigable === false" in app_js
    assert "if (await jumpToNavigationEntry(state.project, entry)) {" in app_js
    assert ".listing-app-slot-typed" in styles_css
