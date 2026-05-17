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


def test_web_app_surfaces_decompression_relationship_roles() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "function payloadRelationshipTooltip(relationship)" in app_js
    assert "function appendDerivedTargetSummary(details, target)" in app_js
    assert "relationship.payload_role" in app_js
    assert "relationship.payload_role_confidence" in app_js
    assert "relationship.parent_remains_active" in app_js
    assert "target.derived_targets" in app_js
    assert "decompressed payload" in app_js
    assert "payloadRelationshipTooltip(origin);" in app_js
    assert "appendDerivedTargetSummary(details, target);" in app_js


def test_web_app_annotation_controls_use_manual_review_actions() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "fallbackEntity" not in app_js
    assert "let entity;" not in app_js
    assert "function reviewItemCatalogActions(item)" in app_js
    assert "data-catalog-action-id" in app_js
    assert 'if (action === "remove_manual_annotation") {' in app_js
    assert ".listing-annotation-edit {\n  opacity: 0;" in styles_css
    assert ".listing-row:hover .listing-annotation-edit" in styles_css
    assert ".listing-row:focus-within .listing-annotation-edit" in styles_css


def test_web_app_command_palette_and_selection_model_are_contextual() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "palette_context_rank" in app_js
    assert "state.commandPalette.global || Number(action.palette_context_rank || 0) === 0" in app_js
    assert 'event.key === "Backspace" && !input.value && !state.commandPalette.global' in app_js
    assert "parameters.struct_name" in app_js
    assert "selection.elementKind = selection.elementSelector?.element_kind || listingElementKind(element);" in app_js
    assert 'setAnalysisStatus("Selection precision lost"' in app_js
    assert "void followSelectedReference(true);" in app_js
    assert 'command === "next_hunk"' in app_js
    assert "function listingSelectionRangeBounds" in app_js
    assert "function resolveRenderedListingRangeSelection" in app_js
    assert "bounds && listingSelectionIsRange(selection) && globalIndex >= bounds.start" in app_js
    assert "function commandPaletteRangeQuery" in app_js
    assert 'params.set("context", "range");' in app_js
    assert "void moveListingSelection(event.key === \"ArrowDown\" ? 1 : -1, event.shiftKey);" in app_js
    assert "listing-row-range-focus" in app_js


def test_web_app_command_palette_uses_schema_parameter_editor() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "const WEB_APP_CONTRACT_VERSION = 2;" in app_js
    assert 'const WEB_APP_CONTRACT_HEADER = "X-Amiga-Web-App-Contract";' in app_js
    assert "function assertWebAppContract(payload)" in app_js
    assert "function verifyWebAppContract()" in app_js
    assert "await verifyWebAppContract();" in app_js
    assert "hard refresh required" in app_js
    assert "function renderCommandParameterEditor(editor)" in app_js
    assert "function commandParameterSchemaFields(action)" in app_js
    assert "function submitCommandParameterEditor()" in app_js
    assert "window.prompt(\"Label name\"" not in app_js
    assert "Unsupported parameter type:" in app_js
    assert 'field.type === "boolean"' in app_js
    assert 'field.type === "number" || field.type === "integer"' in app_js
    assert "field.enumValues.length" in app_js
    assert "submitError" in app_js
    assert "commandPaletteRangeAvailabilityRank" in app_js
    assert "action.availability_reason" in app_js
    assert "function applyManualActionApplication" in app_js
    assert "function applyManualLocalEffect" not in app_js
    assert "function applyManualLabelRenameEffect" not in app_js
    assert "function closeSubmittedParameterSurface" in app_js
    assert "closeSubmittedParameterSurface();" in app_js
    assert "function commandPaletteRowQuery" in app_js
    assert "function listingRowLocator" in app_js
    assert "function commandPaletteElementId" in app_js
    assert 'params.set("locator", JSON.stringify(locator));' in app_js
    assert 'params.set("locators", JSON.stringify(locators));' in app_js
    assert 'manual-action-catalog' not in app_js
    assert 'params.set("rows"' not in app_js
    assert "function manualActionRefreshMode" in app_js
    assert 'mode === "none" || mode === "project" || mode === "analysis"' in app_js
    assert "Server returned incompatible manual action refresh mode" in app_js
    assert "refreshProjectPayloadInBackground" not in app_js
    assert "commandRequiresAnalysisRefresh" not in app_js
    assert "function applyManualReviewNoteAddEffect" not in app_js
    assert "function flashManualActionApplication" in app_js
    assert "function flashManualActionLocations" in app_js
    assert "function manualActionLocationMatchesRow" in app_js
    assert "function showManualReviewActionSaved" in app_js
    assert "function renderReviewNoteBadge" in app_js
    assert "function openInlineParameterSession" in app_js
    assert "function renderInlineParameterSession" in app_js
    assert "function renderParameterChoiceGrid" in app_js
    assert "function renderParameterFilteredChooser" in app_js
    assert "function invokeEditSelectedCommand" in app_js
    assert "function commandLabelValidationError" in app_js
    assert "interaction_schema?.primary_rank" in app_js
    assert "action.action === \"set_representation\") return 2" not in app_js
    assert "validation.local_labels_supported === false" in app_js
    assert '["review-notes", "Review Notes"]' in app_js
    assert "openNavigationOverlay(\"review-notes\", noteId)" in app_js
    assert "state.manualEdit.inFlight" in app_js
    assert "listing-row-manual-pending" in app_js
    assert "listing-row-manual-saved" in app_js
    assert 'setAnalysisStatus("Manual action saved", "ready", 2000)' not in app_js
    assert 'setAnalysisStatus("Manual seed saved", "ready", 2000)' not in app_js
    assert "focusTarget: false" in app_js
    assert ".project-badge-review-note" in styles_css
    assert ".command-parameter-editor" in styles_css
    assert ".command-parameter-field-error" in styles_css
    assert ".listing-row-manual-saved" in styles_css
    assert "@keyframes listing-row-manual-saved" in styles_css


def test_web_app_uses_project_local_ui_preferences_for_listing_location() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "function loadUiPreferenceState(projectId)" in app_js
    assert "function explicitListingLocationFromUrl(projectId)" in app_js
    assert "function listingLocatorFromUrlParams(projectId, value)" in app_js
    assert "function preferenceListingLocation(payload)" in app_js
    assert "function jumpToListingLocator(projectId, locator, viewportAnchor = null)" in app_js
    assert "selection_locator" in app_js
    assert "focus_locator" in app_js
    assert "viewport_anchor" in app_js
    assert 'numericValue("row_index")' not in app_js
    assert 'location.row_index = Math.floor(rowIndex);' not in app_js
    assert '["stableKey", "stable_key"]' not in app_js
    assert '["rowCode", "row_code"]' not in app_js
    assert "function entrypointListingLocations(payload)" in app_js
    assert "function loadInitialListingLocation(projectId, uiPreferences)" in app_js
    assert "function scheduleUiPreferenceSave()" in app_js
    assert "`/api/projects/${encodeURIComponent(projectId)}/ui-preferences`" in app_js
    assert "`/api/projects/${encodeURIComponent(state.project)}/ui-preferences`" in app_js
    assert 'method: "PUT"' in app_js
    assert "state.uiPreferences.restoring" in app_js
    assert "return focusFirstRenderedListingRow();" in app_js
    assert "repaired.projection_hash !== target.projection_hash" in app_js


def test_web_app_initial_listing_load_requests_virtual_window() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "const count = viewport ? listingFetchCount(viewport) : LISTING_INITIAL_ROW_WINDOW;" in app_js
    assert "return loadListingWindow(projectId, null, 0, count, {start: 0, count});" in app_js
    assert "await loadListingWindow(projectId, null, 0, 240);" not in app_js


def test_web_app_typed_navigation_uses_data_class_rows() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "Boolean(row.data_class)" in app_js
    assert "row.comment_text || row.data_class || item.semantic_role" in app_js
    assert "const typedDataSeen = new Set();" in app_js
    assert "if (!typedDataSeen.has(key)) {" in app_js


def test_web_app_generation_refresh_restores_only_applied_request() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "const requestSeqBeforeRefresh = state.virtualListing.requestSeq;" in app_js
    assert "if (!ListingSession.shouldApplyResponse(requestSeqBeforeRefresh + 1)) {" in app_js
    assert "restoreListingAddressAnchor(document.getElementById(\"listing-viewport\"), anchor);" in app_js


def test_web_app_listing_state_uses_internal_models() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "const ListingSession = {" in app_js
    assert "beginRequest()" in app_js
    assert "shouldApplyResponse(requestSeq)" in app_js
    assert "ListingSession.applyWindow(listing);" in app_js
    assert "if (!ListingSession.shouldApplyResponse(requestSeq)) {" in app_js
    assert "const SelectionModel = {" in app_js
    assert "locator," in app_js
    assert "focusLocator: locator" in app_js
    assert "data-row-locator=" in app_js
    assert "listingLocatorsSameRow" in app_js
    assert "const PreferenceSync = {" in app_js
    assert "PreferenceSync.setPayload(await fetchJson" in app_js
    assert "const NavigationSession = {" in app_js
    assert "NavigationSession.applyPayload(payload);" in app_js
    assert "NavigationSession.pushHistory(origin, current);" in app_js
    assert "navigationEntryRecoverable(origin)" in app_js
    assert "storedListingLocator(entry.locator, state.project)" in app_js


def test_web_app_exposes_copied_browser_debug_state_hook() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert "window.__amigaDebugState = browserDebugState;" in app_js
    assert "schema_version: 1" in app_js
    assert "jsonSafeDebugCopy({" in app_js
    assert "owner: \"ProjectSession\"" in app_js
    assert "owner: \"ListingSession\"" in app_js
    assert "owner: \"SelectionModel\"" in app_js
    assert "owner: \"ManualMutationState\"" in app_js
    assert "visible_locators: visibleListingLocators()" in app_js
    assert "selected_locator: storedListingLocator(selection.locator, state.project)" in app_js
    assert "pending_mutation_id" in app_js


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
    assert 'source.addEventListener("listing_artifact_ready"' in app_js
    assert 'setAnalysisStatus("Applying analysis", "running")' in app_js
    assert 'setAnalysisStatus("Analysis ready", "ready", 2000)' in app_js
    assert 'state.analysisStatus.state === "running"' in app_js
    assert ".analysis-status" in styles_css
    assert ".listing-viewport .analysis-status" not in styles_css


def test_web_app_progress_labels_do_not_fail_unknown_job_shapes() -> None:
    app_js = (
        Path(__file__).resolve().parent.parent
        / "amiga_reversing" / "web"
        / "app.js"
    ).read_text(encoding="utf-8")

    assert 'const jobKind = String(job.job_kind || "").trim();' in app_js
    assert 'const phaseId = String(job.phase_id || "").trim();' in app_js
    assert 'return jobKind ? jobKind.replaceAll("_", " ") : "Working";' in app_js
    assert 'return phaseId ? phaseId.replaceAll("_", " ") : "Working";' in app_js
    assert "throw new Error(`Unknown job kind:" not in app_js
    assert "throw new Error(`Unknown ${job.job_kind} phase id:" not in app_js


def test_web_app_exposes_reproduction_badge_panel_and_issue_navigation() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "amiga_reversing" / "web"
    app_js = (web_dir / "app.js").read_text(encoding="utf-8")
    styles_css = (web_dir / "styles.css").read_text(encoding="utf-8")

    assert "function reproductionBadge(ready, report)" in app_js
    assert 'id="open-repro"' in app_js
    assert "function renderReproPanel()" in app_js
    assert "function renderReproductionPolicySummary(report)" in app_js
    assert "function setReproductionProfile(profileId)" in app_js
    assert "async function exportSource(assemblerProfile)" in app_js
    assert "source-export?assembler_profile=" in app_js
    assert "new Blob([sourceText]" in app_js
    assert "source_export_assembler: profile" in app_js
    assert "tool_availability" in app_js
    assert "tool-availability-warning" in app_js
    assert "function renderOracleCompatibility(report)" in app_js
    assert "oracle_compatibility" in app_js
    assert "oracle-result" in styles_css
    assert "function currentReproIssue()" in app_js
    assert "function reproductionReportKey(report)" in app_js
    assert "const previousReportKey = state.reproduction.reportKey || reproductionReportKey(state.reproduction.report);" in app_js
    assert "state.reproduction.reportKey = null;" in app_js
    assert "state.reproduction.reportKey = reproductionReportKey(state.reproduction.report);" in app_js
    assert "state.reproduction.selectedIssueEntry = entry;" in app_js
    assert '`/api/projects/${encodeURIComponent(projectId)}/reproduction/run`' in app_js
    assert '`/api/projects/${encodeURIComponent(state.project)}/reproduction/profile`' in app_js
    assert "target-edits" not in app_js
    assert "data-repro-edit-kind" not in app_js
    assert "applyManualLocalEffect" not in app_js
    assert 'return {label: "Unsupported"' in app_js
    assert '"repro-issues": []' in app_js
    assert '["repro-issues", "Repro Issues"]' in app_js
    assert "listing-row-repro-issue" in app_js
    assert ".repro-panel" in styles_css
    assert ".repro-policy-summary" in styles_css
    assert ".tool-availability-warning" in styles_css
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
