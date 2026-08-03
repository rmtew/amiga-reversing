from pathlib import Path

from src.scripts.compare_corpus_artifacts import NORMAL_ARTIFACT_NAMES, compare_normal_artifacts


def _write_artifacts(directory: Path, *, suffix: bytes = b"") -> None:
    directory.mkdir()
    for index, name in enumerate(NORMAL_ARTIFACT_NAMES):
        (directory / name).write_bytes(f"artifact-{index}".encode() + suffix)


def test_compare_normal_artifacts_requires_all_declared_artifacts_and_bytes(tmp_path: Path) -> None:
    oracle = tmp_path / "oracle"
    candidate = tmp_path / "candidate"
    _write_artifacts(oracle)
    _write_artifacts(candidate)
    assert {item.status for item in compare_normal_artifacts(oracle, candidate)} == {"identical"}

    (candidate / NORMAL_ARTIFACT_NAMES[3]).write_bytes(b"different")
    comparisons = compare_normal_artifacts(oracle, candidate)
    assert next(item for item in comparisons if item.name == NORMAL_ARTIFACT_NAMES[3]).status == "different"

    (candidate / NORMAL_ARTIFACT_NAMES[5]).unlink()
    comparisons = compare_normal_artifacts(oracle, candidate)
    assert next(item for item in comparisons if item.name == NORMAL_ARTIFACT_NAMES[5]).status == "missing"
