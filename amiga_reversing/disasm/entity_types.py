from __future__ import annotations

from typing import NotRequired, TypedDict


class EntityRecord(TypedDict):
    addr: str
    type: str
    end: NotRequired[str]
    hunk: NotRequired[int]
    name: NotRequired[str]
    comment: NotRequired[str]
    subtype: NotRequired[str]
    confidence: NotRequired[str]


class EntityPatch(TypedDict, total=False):
    name: str
    comment: str
    type: str
    subtype: str
    confidence: str


class OverridesPayload(TypedDict):
    entities: dict[str, EntityPatch]
