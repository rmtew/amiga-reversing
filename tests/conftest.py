from __future__ import annotations

from collections.abc import Callable
from typing import cast

from disasm.types import HunkDisassemblySession
import pytest

from disasm.projects import build_project_session


def _bloodwych_hunk_session() -> HunkDisassemblySession:
    return build_project_session("bloodwych").hunk_sessions[0]


bloodwych_hunk_session = cast(
    Callable[[], HunkDisassemblySession],
    pytest.fixture(scope="session")(_bloodwych_hunk_session),
)
