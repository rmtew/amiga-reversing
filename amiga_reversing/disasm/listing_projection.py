from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Protocol, cast

from amiga_reversing.disasm.api import ListingWindowPayload


class ListingArtifactLike(Protocol):
    def close(self) -> None: ...


class ListingLocatorError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ListingRowLocator:
    target_id: str
    projection_hash: str
    row_key: str
    section_index: int | None
    start_offset: int | None
    end_offset: int | None
    kind: str
    storage_address: int | None = None
    runtime_address: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "target_id": self.target_id,
            "projection_hash": self.projection_hash,
            "row_key": self.row_key,
            "section_index": self.section_index,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "kind": self.kind,
            "storage_address": self.storage_address,
            "runtime_address": self.runtime_address,
        }

    @classmethod
    def from_mapping(cls, payload: object) -> ListingRowLocator:
        if not isinstance(payload, dict):
            raise ListingLocatorError("missing_locator", "locator must be an object")
        locator = cast(dict[str, object], payload)
        return cls(
            target_id=_required_str(locator, "target_id"),
            projection_hash=_required_str(locator, "projection_hash"),
            row_key=_required_str(locator, "row_key"),
            section_index=_optional_int(locator.get("section_index")),
            start_offset=_optional_int(locator.get("start_offset")),
            end_offset=_optional_int(locator.get("end_offset")),
            kind=_required_str(locator, "kind"),
            storage_address=_optional_int(locator.get("storage_address")),
            runtime_address=_optional_int(locator.get("runtime_address")),
        )


class ListingProjectionService:
    def __init__(self) -> None:
        self._artifacts: dict[str, ListingArtifactLike] = {}
        self._cache_keys: dict[str, str] = {}
        self._presentation_dirty: set[str] = set()
        self._review_items_cache: dict[str, tuple[str, int, tuple[dict[str, object], ...]]] = {}
        self._row_indexes: dict[
            str,
            tuple[
                str,
                dict[str, dict[str, object]],
                dict[tuple[int | None, int | None, int | None, str], list[dict[str, object]]],
            ],
        ] = {}

    def debug_state(self) -> dict[str, object]:
        return {
            "artifact_projects": sorted(self._artifacts),
            "cache_keys": dict(sorted(self._cache_keys.items())),
            "presentation_dirty_projects": sorted(self._presentation_dirty),
            "review_item_cache_projects": sorted(self._review_items_cache),
            "row_index_projects": sorted(self._row_indexes),
        }

    def reset(self) -> None:
        for artifact in self._artifacts.values():
            _close_artifact(artifact)
        self._artifacts.clear()
        self._cache_keys.clear()
        self._presentation_dirty.clear()
        self._review_items_cache.clear()
        self._row_indexes.clear()

    def clear_project(self, project_id: str) -> None:
        artifact = self._artifacts.pop(project_id, None)
        if artifact is not None:
            _close_artifact(artifact)
        self._cache_keys.pop(project_id, None)
        self._presentation_dirty.discard(project_id)
        self._review_items_cache.pop(project_id, None)
        self._row_indexes.pop(project_id, None)

    def invalidate_project_keep_artifact(self, project_id: str) -> None:
        if project_id in self._artifacts:
            self._cache_keys[project_id] = f"__invalidated__:{project_id}"
            self._presentation_dirty.add(project_id)
        else:
            self._cache_keys.pop(project_id, None)
            self._presentation_dirty.discard(project_id)
        self._review_items_cache.pop(project_id, None)
        self._row_indexes.pop(project_id, None)

    def mark_presentation_dirty(self, project_id: str) -> None:
        self._presentation_dirty.add(project_id)

    def is_presentation_dirty(self, project_id: str) -> bool:
        return project_id in self._presentation_dirty

    def set_artifact(
        self,
        *,
        project_id: str,
        cache_key: str,
        artifact: ListingArtifactLike,
    ) -> None:
        old_artifact = self._artifacts.get(project_id)
        self._cache_keys[project_id] = cache_key
        self._artifacts[project_id] = artifact
        self._presentation_dirty.discard(project_id)
        self._review_items_cache.pop(project_id, None)
        self._row_indexes.pop(project_id, None)
        if old_artifact is not None and old_artifact is not artifact:
            _close_artifact(old_artifact)

    def seed_artifact_for_test(
        self,
        project_id: str,
        artifact: ListingArtifactLike,
        *,
        cache_key: str = "cache",
    ) -> None:
        self.set_artifact(project_id=project_id, cache_key=cache_key, artifact=artifact)

    def artifact_for_test(self, project_id: str) -> ListingArtifactLike | None:
        return self._artifacts.get(project_id)

    def cache_key_for_test(self, project_id: str) -> str | None:
        return self._cache_keys.get(project_id)

    def has_project_state(self, project_id: str) -> bool:
        return project_id in self._cache_keys or project_id in self._artifacts

    def seed_cache_key_for_test(self, project_id: str, *, cache_key: str) -> None:
        self._cache_keys[project_id] = cache_key

    def cache_satisfies_listing(self, project_id: str, cache_key: str) -> bool:
        return self._cache_keys.get(project_id) == cache_key and self._artifacts.get(project_id) is not None

    def valid_artifact(self, project_id: str, current_cache_key: str) -> ListingArtifactLike | None:
        artifact = self._artifacts.get(project_id)
        cached_key = self._cache_keys.get(project_id)
        if cached_key is None:
            return None
        if cached_key != current_cache_key:
            if artifact is not None and project_id in self._presentation_dirty:
                return None
            self.clear_project(project_id)
            return None
        return artifact

    def read_artifact(self, project_id: str, current_cache_key: str) -> ListingArtifactLike | None:
        artifact = self.valid_artifact(project_id, current_cache_key)
        if artifact is not None:
            return artifact
        if project_id in self._presentation_dirty:
            return self._artifacts.get(project_id)
        return None

    def cached_analysis_review_items(
        self,
        *,
        project_id: str,
        artifact: object,
        item_factory: Callable[[dict[str, object]], list[dict[str, object]]],
    ) -> tuple[dict[str, object], ...]:
        cache_key = self._cache_keys.get(project_id)
        if cache_key is None:
            return ()
        artifact_id = id(artifact)
        cached = self._review_items_cache.get(project_id)
        if cached is not None and cached[0] == cache_key and cached[1] == artifact_id:
            return cached[2]
        analysis_payload_fn = getattr(artifact, "analysis_payload", None)
        if not callable(analysis_payload_fn):
            return ()
        analysis_payload, _ = analysis_payload_fn()
        items = tuple(item_factory(cast(dict[str, object], analysis_payload)))
        self._review_items_cache[project_id] = (cache_key, artifact_id, items)
        return items

    def projection_hash(self, *, project_id: str, current_cache_key: str) -> str:
        cached_key = self._cache_keys.get(project_id)
        return cached_key if cached_key == current_cache_key else current_cache_key

    def listing_artifact_ready_event(self, *, project_id: str, total_rows: int) -> dict[str, object]:
        return {
            "_event_type": "listing_artifact_ready",
            "project_id": project_id,
            "total_rows": total_rows,
            "changed_ranges": [],
        }

    def cancel_listing_jobs(
        self,
        *,
        jobs: dict[str, dict[str, object]],
        lock: Any,
        job_kind: str,
        now: Callable[[], float],
        project_id: str | None = None,
    ) -> list[tuple[str, dict[str, object]]]:
        canceled: list[tuple[str, dict[str, object]]] = []
        with lock:
            stale_job_ids = [
                job_id
                for job_id, job in jobs.items()
                if job.get("job_kind") == job_kind
                and (project_id is None or job.get("project_id") == project_id)
            ]
            for job_id in stale_job_ids:
                job = dict(jobs[job_id])
                job["status"] = "failed"
                job["phase_id"] = "error"
                job["error"] = "job canceled"
                job["finished_at"] = now()
                canceled.append((job_id, dict(job)))
                del jobs[job_id]
        return canceled

    def start_listing_job(
        self,
        *,
        project_id: str,
        cache_key: str,
        jobs: dict[str, dict[str, object]],
        lock: Any,
        job_kind: str,
        phase_count: int,
        now: Callable[[], float],
        make_job_id: Callable[[], str],
        total_rows: Callable[[], int | None],
        prewarm: Callable[[], None],
        on_ready: Callable[[], None],
        start_worker: Callable[[str, str], None],
    ) -> dict[str, object]:
        if self.cache_satisfies_listing(project_id, cache_key):
            prewarm()
            job_id = f"cached-listing-artifact-{project_id}"
            timestamp = now()
            payload: dict[str, object] = {
                "job_id": job_id,
                "job_kind": job_kind,
                "project_id": project_id,
                "result_project_id": project_id,
                "status": "ready",
                "phase_id": "done",
                "phase_index": phase_count,
                "phase_count": phase_count,
                "progress_mode": "determinate",
                "progress_current": phase_count,
                "progress_total": phase_count,
                "progress_percent": 100,
                "total_rows": total_rows(),
                "error": None,
                "created_at": timestamp,
                "finished_at": timestamp,
                "cache_key": cache_key,
            }
            with lock:
                jobs[job_id] = dict(payload)
            on_ready()
            return payload

        with lock:
            for job in jobs.values():
                if (
                    job.get("job_kind") == job_kind
                    and job.get("project_id") == project_id
                    and job.get("cache_key") == cache_key
                    and job.get("status") in {"queued", "building"}
                ):
                    return dict(job)
            job_id = make_job_id()
            jobs[job_id] = {
                "job_id": job_id,
                "job_kind": job_kind,
                "project_id": project_id,
                "result_project_id": project_id,
                "status": "queued",
                "phase_id": "queued",
                "phase_index": 0,
                "phase_count": phase_count,
                "progress_mode": "determinate",
                "progress_current": 0,
                "progress_total": phase_count,
                "progress_percent": 0,
                "total_rows": None,
                "error": None,
                "created_at": now(),
                "finished_at": None,
                "cache_key": cache_key,
            }
        start_worker(job_id, project_id)
        with lock:
            return dict(jobs[job_id])

    def normalize_window(
        self,
        *,
        target_id: str,
        projection_hash: str,
        payload: ListingWindowPayload,
    ) -> ListingWindowPayload:
        rows = [
            self.normalize_row(target_id=target_id, projection_hash=projection_hash, row=row)
            for row in payload["rows"]
        ]
        self._index_rows(target_id=target_id, projection_hash=projection_hash, rows=rows)
        return cast(ListingWindowPayload, {**payload, "target_id": target_id, "projection_hash": projection_hash, "rows": rows})

    def normalize_row(self, *, target_id: str, projection_hash: str, row: dict[str, object]) -> dict[str, object]:
        locator = self.locator_for_row(target_id=target_id, projection_hash=projection_hash, row=row)
        normalized = dict(row)
        normalized.pop("row_id", None)
        normalized.pop("stable_key", None)
        normalized.pop("stableKey", None)
        normalized.update(locator.to_dict())
        normalized["locator"] = locator.to_dict()
        return normalized

    def locator_for_row(self, *, target_id: str, projection_hash: str, row: dict[str, object]) -> ListingRowLocator:
        storage_address = _optional_int(row.get("storage_address"))
        if storage_address is None:
            storage_address = _optional_int(row.get("addr"))
        return ListingRowLocator(
            target_id=target_id,
            projection_hash=projection_hash,
            row_key=_row_key(row),
            section_index=_optional_int(row.get("section_index")),
            start_offset=_optional_int(row.get("start_offset")),
            end_offset=_optional_int(row.get("end_offset")),
            kind=_required_str(row, "kind"),
            storage_address=storage_address,
            runtime_address=_optional_int(row.get("runtime_address")),
        )

    def resolve_locator(
        self,
        *,
        target_id: str,
        projection_hash: str,
        rows: list[dict[str, object]],
        locator_payload: object,
    ) -> dict[str, object]:
        locator = ListingRowLocator.from_mapping(locator_payload)
        if locator.target_id != target_id:
            raise ListingLocatorError("target_mismatch", "locator target_id does not match route target")
        normalized_rows = [
            self.normalize_row(target_id=target_id, projection_hash=projection_hash, row=row)
            for row in rows
        ]
        if locator.projection_hash == projection_hash:
            for row in normalized_rows:
                if row.get("row_key") == locator.row_key:
                    return row
            raise ListingLocatorError("missing_locator", "locator row_key is not in current projection")
        candidates = [
            row
            for row in normalized_rows
            if row.get("section_index") == locator.section_index
            and row.get("start_offset") == locator.start_offset
            and row.get("end_offset") == locator.end_offset
            and row.get("kind") == locator.kind
        ]
        if not candidates:
            raise ListingLocatorError("missing_locator", "stale locator recovery found no row")
        if len(candidates) > 1:
            raise ListingLocatorError("ambiguous_locator", "stale locator recovery matched multiple rows")
        return candidates[0]

    def resolve_locator_from_artifact(
        self,
        *,
        target_id: str,
        projection_hash: str,
        artifact: object,
        locator_payload: object,
    ) -> dict[str, object]:
        locator = ListingRowLocator.from_mapping(locator_payload)
        if locator.target_id != target_id:
            raise ListingLocatorError("target_mismatch", "locator target_id does not match route target")
        indexed = self._indexed_locator_row(
            target_id=target_id,
            projection_hash=projection_hash,
            locator=locator,
        )
        if indexed is not None:
            return indexed
        row = self._artifact_locator_row(
            target_id=target_id,
            projection_hash=projection_hash,
            artifact=artifact,
            locator=locator,
        )
        if row is None:
            if locator.projection_hash == projection_hash:
                raise ListingLocatorError("missing_locator", "locator row_key is not in current projection")
            raise ListingLocatorError("missing_locator", "stale locator recovery found no row")
        return row

    def _index_rows(
        self,
        *,
        target_id: str,
        projection_hash: str,
        rows: list[dict[str, object]],
    ) -> None:
        by_key: dict[str, dict[str, object]] = {}
        by_identity: dict[tuple[int | None, int | None, int | None, str], list[dict[str, object]]] = {}
        for row in rows:
            key = row.get("row_key")
            if isinstance(key, str) and key:
                by_key[key] = dict(row)
            by_identity.setdefault(_recovery_identity(row), []).append(dict(row))
        self._row_indexes[target_id] = (projection_hash, by_key, by_identity)

    def _indexed_locator_row(
        self,
        *,
        target_id: str,
        projection_hash: str,
        locator: ListingRowLocator,
    ) -> dict[str, object] | None:
        indexed = self._row_indexes.get(target_id)
        if indexed is None or indexed[0] != projection_hash:
            return None
        by_key = indexed[1]
        if locator.projection_hash == projection_hash:
            row = by_key.get(locator.row_key)
            return dict(row) if row is not None else None
        candidates = indexed[2].get(_locator_recovery_identity(locator), [])
        if len(candidates) > 1:
            raise ListingLocatorError("ambiguous_locator", "stale locator recovery matched multiple rows")
        return dict(candidates[0]) if candidates else None

    def _artifact_locator_row(
        self,
        *,
        target_id: str,
        projection_hash: str,
        artifact: object,
        locator: ListingRowLocator,
    ) -> dict[str, object] | None:
        rows = getattr(artifact, "rows", None)
        if isinstance(rows, list):
            materialized_rows = [
                _artifact_row_dict(row, row_index=index)
                for index, row in enumerate(rows)
            ]
            return self.resolve_locator(
                target_id=target_id,
                projection_hash=projection_hash,
                rows=materialized_rows,
                locator_payload=locator.to_dict(),
            )
        row_for_source_offset = getattr(artifact, "row_for_source_offset", None)
        if not callable(row_for_source_offset) or locator.start_offset is None:
            return self._single_row_artifact_locator_row(
                target_id=target_id,
                projection_hash=projection_hash,
                artifact=artifact,
                locator=locator,
            )
        row = row_for_source_offset(section_index=locator.section_index, offset=locator.start_offset)
        if not isinstance(row, dict):
            return self._single_row_artifact_locator_row(
                target_id=target_id,
                projection_hash=projection_hash,
                artifact=artifact,
                locator=locator,
            )
        normalized = self.normalize_row(target_id=target_id, projection_hash=projection_hash, row=dict(row))
        if locator.projection_hash == projection_hash:
            if normalized.get("row_key") == locator.row_key:
                return normalized
        elif _recovery_identity(normalized) == _locator_recovery_identity(locator):
            return normalized

        # A source offset can have a projected label immediately before its
        # backing data/instruction row.  C artifacts resolve the offset to the
        # backing row, so a locator issued for that label cannot be recovered
        # from the single-row lookup alone after its listing window has been
        # evicted from the projection index.  Re-read a bounded neighborhood
        # from the same artifact so public listing locators remain executable.
        window_payload = getattr(artifact, "window_payload", None)
        row_index = _optional_int(row.get("row_index"))
        if not callable(window_payload) or row_index is None:
            return None
        payload, _profile = window_payload(start=max(0, row_index - 64), count=129)
        window_rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(window_rows, list):
            return None
        materialized_rows = [
            _artifact_row_dict(candidate, row_index=index)
            for index, candidate in enumerate(window_rows, start=max(0, row_index - 64))
        ]
        try:
            return self.resolve_locator(
                target_id=target_id,
                projection_hash=projection_hash,
                rows=materialized_rows,
                locator_payload=locator.to_dict(),
            )
        except ListingLocatorError:
            return None

    def _single_row_artifact_locator_row(
        self,
        *,
        target_id: str,
        projection_hash: str,
        artifact: object,
        locator: ListingRowLocator,
    ) -> dict[str, object] | None:
        summary_payload = getattr(artifact, "summary_payload", None)
        window_payload = getattr(artifact, "window_payload", None)
        if not callable(summary_payload) or not callable(window_payload):
            return None
        summary, _ = summary_payload()
        if summary.get("total_rows") != 1:
            return None
        payload, _ = window_payload(start=0, count=1)
        rows = payload.get("rows") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
            return None
        return self.resolve_locator(
            target_id=target_id,
            projection_hash=projection_hash,
            rows=[dict(cast(dict[str, object], rows[0]))],
            locator_payload=locator.to_dict(),
        )


def _artifact_row_dict(row: object, *, row_index: int) -> dict[str, object]:
    if isinstance(row, dict):
        payload = dict(cast(dict[str, object], row))
    elif is_dataclass(row):
        payload = cast(dict[str, object], asdict(cast(Any, row)))
    else:
        payload = {
            "row_key": getattr(row, "stable_key", None) or getattr(row, "row_id", None),
            "kind": getattr(row, "kind", None),
            "section_index": getattr(row, "section_index", None),
            "start_offset": getattr(row, "start_offset", None),
            "end_offset": getattr(row, "end_offset", None),
            "addr": getattr(row, "addr", None),
            "runtime_address": getattr(row, "runtime_address", None),
            "text": getattr(row, "text", None),
        }
    payload.setdefault("row_index", row_index)
    if not payload.get("row_key"):
        payload["row_key"] = payload.get("stable_key") or payload.get("row_id")
    row_bytes = payload.get("bytes")
    if isinstance(row_bytes, bytes):
        payload["bytes"] = row_bytes.hex()
    return payload


def _recovery_identity(row: dict[str, object]) -> tuple[int | None, int | None, int | None, str]:
    return (
        _optional_int(row.get("section_index")),
        _optional_int(row.get("start_offset")),
        _optional_int(row.get("end_offset")),
        _required_str(row, "kind"),
    )


def _locator_recovery_identity(locator: ListingRowLocator) -> tuple[int | None, int | None, int | None, str]:
    return (locator.section_index, locator.start_offset, locator.end_offset, locator.kind)


def _row_key(row: dict[str, object]) -> str:
    for key in ("row_key", "stable_key", "row_id"):
        value = row.get(key)
        if isinstance(value, str) and value:
            return value
    raise ListingLocatorError("missing_locator", "listing row has no authoritative row identity")


def _required_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ListingLocatorError("missing_locator", f"{key} is required")
    return value


def _optional_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _close_artifact(artifact: object) -> None:
    close = getattr(artifact, "close", None)
    if callable(close):
        close()
