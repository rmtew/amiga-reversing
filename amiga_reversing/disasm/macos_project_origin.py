"""Classic Mac OS project origin identifiers."""

from __future__ import annotations

from collections.abc import Mapping

MACOS_PROJECT_ORIGIN_KIND = "macos_mpw_fixture"


def is_macos_project_origin(origin: Mapping[str, object]) -> bool:
    return origin.get("kind") == MACOS_PROJECT_ORIGIN_KIND
