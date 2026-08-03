from pathlib import Path

import pytest

from src.scripts.run_corpus_projection_conformance import ARTIFACT_ARGUMENTS, _build_command, _require_fresh_directory


def test_conformance_command_uses_explicit_code_data_and_artifact_roots(tmp_path: Path) -> None:
    output = tmp_path / "output"
    command = _build_command(
        python_executable="python", code_root=tmp_path / "oracle-code", data_root=tmp_path / "data",
        output_dir=output, workers=8,
    )
    assert command[:2] == ["python", "-c"]
    child = command[2]
    assert "sys.path.insert(0, str(code_root))" in child
    assert "platform_manifest_io.ROOT = data_root" in child
    assert "--workers', '8'" in child
    for _option, relative_path in ARTIFACT_ARGUMENTS:
        assert repr(str(output / relative_path)) in child


def test_conformance_runner_never_reuses_an_output_directory(tmp_path: Path) -> None:
    output = tmp_path / "output"
    _require_fresh_directory(output)
    with pytest.raises(ValueError, match="refusing to reuse"):
        _require_fresh_directory(output)
