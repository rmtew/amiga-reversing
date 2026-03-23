from __future__ import annotations

from collections.abc import Callable
from typing import cast

import pytest

from disasm.projects import build_project_session
from disasm.types import HunkDisassemblySession


def _bloodwych_hunk_session() -> HunkDisassemblySession:
    return build_project_session("bloodwych").hunk_sessions[0]


bloodwych_hunk_session = cast(
    Callable[[], HunkDisassemblySession],
    pytest.fixture(scope="session")(_bloodwych_hunk_session),
)
