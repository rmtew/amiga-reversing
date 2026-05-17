from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from amiga_reversing.disasm.api import ListingWindowPayload


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
