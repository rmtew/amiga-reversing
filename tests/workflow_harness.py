from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, slots=True)
class ManualWorkflowExpectation:
    project_id: str
    manual_action_log_count: int
    durable_action_id: str | None = None
    row_key: str | None = None
    projection_hash: str | None = None
    comment_text: str | None = None
    review_title: str | None = None
    review_state: str | None = None
    presentation_dirty: bool | None = None
    locator_recovered: bool | None = None
    workflow_spans: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class PreferenceWorkflowExpectation:
    project_id: str
    source_export_assembler: str | None = None
    listing_row_key: str | None = None


@dataclass(frozen=True, slots=True)
class DurabilityBoundary:
    name: str
    required: bool = True
    transient_reason: str | None = None
    prepare: Callable[[], None] | None = None


def assert_manual_workflow_snapshot(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    mutation = _mapping(snapshot.get("mutation"), "durable state: missing mutation")
    _assert_manual_log_state(mutation, expected)
    _assert_project_manual_state(snapshot, expected)
    _assert_listing_projection(snapshot, expected)
    _assert_locator_recovery(snapshot, expected)
    _assert_debug_state(snapshot, expected)
    _assert_workflow_profile(snapshot, expected)


def assert_preference_workflow_snapshot(
    snapshot: Mapping[str, object],
    expected: PreferenceWorkflowExpectation,
) -> None:
    preferences_payload = _mapping(snapshot.get("preferences"), "durable state: missing preferences")
    preferences = _mapping(preferences_payload.get("preferences"), "durable state: missing preference body")
    if preferences.get("target_id") != expected.project_id:
        raise AssertionError("durable state: preference target_id mismatch")
    if preferences.get("source_export_assembler") != expected.source_export_assembler:
        raise AssertionError("durable state: source export assembler preference mismatch")
    if expected.listing_row_key is not None:
        location = _mapping(preferences.get("listing_location"), "durable state: missing listing location")
        locator = _mapping(location.get("locator"), "durable state: missing listing locator")
        if locator.get("row_key") != expected.listing_row_key:
            raise AssertionError("durable state: listing location row_key mismatch")
    _assert_preference_debug_state(snapshot, expected)


def run_durability_matrix(
    boundaries: Iterable[DurabilityBoundary],
    snapshot_factory: Callable[[DurabilityBoundary], Mapping[str, object]],
    assertion: Callable[[Mapping[str, object]], None],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for boundary in boundaries:
        if not boundary.required:
            if not boundary.transient_reason:
                raise AssertionError(f"durability boundary {boundary.name}: transient boundary needs a reason")
            results.append({"boundary": boundary.name, "status": "transient", "reason": boundary.transient_reason})
            continue
        if boundary.prepare is not None:
            boundary.prepare()
        try:
            assertion(snapshot_factory(boundary))
        except AssertionError as exc:
            raise AssertionError(f"durability boundary {boundary.name}: {exc}") from exc
        results.append({"boundary": boundary.name, "status": "passed"})
    return results


def _assert_manual_log_state(
    mutation: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    if mutation.get("manual_action_log_count") != expected.manual_action_log_count:
        raise AssertionError("durable state: manual action log count mismatch")
    head_hash = mutation.get("manual_action_log_head_hash")
    if not isinstance(head_hash, str) or len(head_hash) != 64:
        raise AssertionError("durable state: manual action log head hash missing")
    metadata_hash = mutation.get("effective_metadata_hash")
    if not isinstance(metadata_hash, str) or len(metadata_hash) != 64:
        raise AssertionError("durable state: effective metadata hash missing")
    if expected.durable_action_id is not None and mutation.get("durable_action_id") != expected.durable_action_id:
        raise AssertionError("durable state: durable action id mismatch")
    if expected.projection_hash is not None and mutation.get("projection_hash") != expected.projection_hash:
        raise AssertionError("projection: mutation projection hash mismatch")
    if expected.row_key is not None:
        locators = mutation.get("affected_locators")
        if not isinstance(locators, list) or not any(
            isinstance(locator, dict) and locator.get("row_key") == expected.row_key
            for locator in locators
        ):
            raise AssertionError("locator recovery: affected locator row_key mismatch")


def _assert_project_manual_state(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    project_payload = _mapping(snapshot.get("project"), "durable state: missing project payload")
    project = _mapping(project_payload.get("project"), "durable state: missing project body")
    manual_state = _mapping(project.get("manual_state"), "durable state: missing manual state")
    if expected.review_state is not None and project.get("review_state") != expected.review_state:
        raise AssertionError("durable state: review state mismatch")
    if expected.comment_text is not None and not _contains_entry(manual_state.get("comments"), "text", expected.comment_text):
        raise AssertionError("durable state: manual comment not reloaded")
    if expected.review_title is not None and not _contains_entry(manual_state.get("review_notes"), "title", expected.review_title):
        raise AssertionError("durable state: review note not reloaded")


def _assert_listing_projection(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    listing = _mapping(snapshot.get("listing"), "projection: missing listing payload")
    rows = listing.get("rows")
    if not isinstance(rows, list):
        raise AssertionError("projection: listing rows missing")
    row = _row_by_key(rows, expected.row_key)
    if expected.comment_text is not None and row.get("comment_text") != expected.comment_text:
        raise AssertionError("projection: comment text missing from listing row")
    if expected.review_title is not None:
        annotations = row.get("view_annotations")
        if not isinstance(annotations, list) or not any(expected.review_title in str(item) for item in annotations):
            raise AssertionError("projection: review note missing from listing row")


def _assert_locator_recovery(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    if expected.locator_recovered is None:
        return
    recovery = _mapping(snapshot.get("locator_recovery"), "locator recovery: missing recovery snapshot")
    if recovery.get("ok") is not expected.locator_recovered:
        raise AssertionError("locator recovery: status mismatch")
    if expected.projection_hash is not None and recovery.get("projection_hash") != expected.projection_hash:
        raise AssertionError("locator recovery: projection hash mismatch")
    if expected.row_key is not None and recovery.get("row_key") != expected.row_key:
        raise AssertionError("locator recovery: row_key mismatch")


def _assert_debug_state(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    server_debug = _mapping(snapshot.get("server_debug_state"), "debug state: missing server debug state")
    if expected.project_id not in cast(list[object], server_debug.get("artifact_projects", [])):
        raise AssertionError("debug state: listing artifact project missing")
    cache_keys = _mapping(server_debug.get("cache_keys"), "debug state: cache keys missing")
    if expected.projection_hash is not None and cache_keys.get(expected.project_id) != expected.projection_hash:
        raise AssertionError("debug state: listing cache key mismatch")
    if expected.presentation_dirty is not None:
        dirty = expected.project_id in cast(list[object], server_debug.get("presentation_dirty_projects", []))
        if dirty is not expected.presentation_dirty:
            raise AssertionError("debug state: presentation dirty mismatch")
    browser_debug = snapshot.get("browser_debug_state")
    if browser_debug is not None:
        browser = _mapping(browser_debug, "debug state: malformed browser debug state")
        if browser.get("project_id") != expected.project_id:
            raise AssertionError("debug state: browser project mismatch")
        if expected.row_key is not None and browser.get("selected_row_key") != expected.row_key:
            raise AssertionError("debug state: browser selected row mismatch")
        if expected.projection_hash is not None and browser.get("listing_projection_hash") != expected.projection_hash:
            raise AssertionError("debug state: browser projection hash mismatch")


def _assert_workflow_profile(
    snapshot: Mapping[str, object],
    expected: ManualWorkflowExpectation,
) -> None:
    if expected.workflow_spans is None:
        return
    workflow_profile = _mapping(snapshot.get("workflow_profile"), "workflow profile: missing workflow profile")
    if workflow_profile.get("workflow_id") != "manual_command_execution":
        raise AssertionError("workflow profile: workflow_id mismatch")
    if workflow_profile.get("target_id") != expected.project_id:
        raise AssertionError("workflow profile: target_id mismatch")
    spans = workflow_profile.get("spans")
    if not isinstance(spans, list):
        raise AssertionError("workflow profile: spans missing")
    span_names = [
        span.get("name")
        for span in spans
        if isinstance(span, dict)
    ]
    for name in expected.workflow_spans:
        if name not in span_names:
            raise AssertionError(f"workflow profile: missing span {name}")


def _assert_preference_debug_state(
    snapshot: Mapping[str, object],
    expected: PreferenceWorkflowExpectation,
) -> None:
    browser_debug = snapshot.get("browser_debug_state")
    if browser_debug is None:
        return
    browser = _mapping(browser_debug, "debug state: malformed browser debug state")
    if browser.get("project_id") != expected.project_id:
        raise AssertionError("debug state: browser project mismatch")
    if expected.listing_row_key is not None and browser.get("selected_row_key") != expected.listing_row_key:
        raise AssertionError("debug state: browser listing row_key mismatch")


def _row_by_key(rows: list[object], row_key: str | None) -> Mapping[str, object]:
    if row_key is None:
        for row in rows:
            if isinstance(row, dict):
                return cast(Mapping[str, object], row)
        raise AssertionError("projection: listing rows missing")
    for row in rows:
        if isinstance(row, dict) and row.get("row_key") == row_key:
            return cast(Mapping[str, object], row)
    raise AssertionError("projection: expected row_key missing")


def _contains_entry(entries: object, key: str, value: object) -> bool:
    return isinstance(entries, list | tuple) and any(
        isinstance(entry, dict) and entry.get(key) == value
        for entry in entries
    )


def _mapping(value: object, message: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise AssertionError(message)
    return cast(Mapping[str, object], value)
