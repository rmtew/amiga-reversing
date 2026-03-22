import pytest

from disasm.projects import build_project_session


@pytest.fixture(scope="session")
def bloodwych_hunk_session():
    return build_project_session("bloodwych").hunk_sessions[0]
