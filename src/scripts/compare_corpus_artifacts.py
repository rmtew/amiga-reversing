"""Check byte identity of the normal corpus-projection artifacts.

The migration gates use this helper rather than ad-hoc shell comparisons so a
candidate and its temporary oracle are assessed against the same explicit
contract.  Build profiles and progress snapshots are deliberately excluded:
they are measurement evidence, not semantic corpus artifacts.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Sequence


NORMAL_ARTIFACT_NAMES = (
    "target_usage_manifest.jsonl",
    "target_usage_xrefs.jsonl",
    "target_usage_snippet_rows.index.jsonl",
    "target_usage_snippet_rows.blob",
    "target_variant_index.jsonl",
    "target_type_flow_report.jsonl",
    "target_unresolved_typed_fields.jsonl",
    "target_usage_coverage.json",
)


@dataclass(frozen=True)
class ArtifactComparison:
    name: str
    status: str
    oracle_size: int | None
    candidate_size: int | None
    oracle_sha256: str | None
    candidate_sha256: str | None


def _digest(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def compare_normal_artifacts(oracle_dir: Path, candidate_dir: Path) -> list[ArtifactComparison]:
    """Compare every normal artifact, including the two-part snippet output."""
    comparisons: list[ArtifactComparison] = []
    for name in NORMAL_ARTIFACT_NAMES:
        oracle_path = oracle_dir / name
        candidate_path = candidate_dir / name
        oracle_exists = oracle_path.is_file()
        candidate_exists = candidate_path.is_file()
        if not oracle_exists or not candidate_exists:
            comparisons.append(ArtifactComparison(
                name, "missing", oracle_path.stat().st_size if oracle_exists else None,
                candidate_path.stat().st_size if candidate_exists else None, None, None,
            ))
            continue
        oracle_digest = _digest(oracle_path)
        candidate_digest = _digest(candidate_path)
        comparisons.append(ArtifactComparison(
            name, "identical" if oracle_digest == candidate_digest else "different",
            oracle_path.stat().st_size, candidate_path.stat().st_size, oracle_digest, candidate_digest,
        ))
    return comparisons


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("oracle", type=Path, help="Clean temporary output from the migration oracle")
    parser.add_argument("candidate", type=Path, help="Clean temporary output from the candidate")
    args = parser.parse_args(argv)
    comparisons = compare_normal_artifacts(args.oracle, args.candidate)
    for comparison in comparisons:
        print(f"{comparison.name}: {comparison.status}")
    return 0 if all(comparison.status == "identical" for comparison in comparisons) else 1


if __name__ == "__main__":
    raise SystemExit(main())
