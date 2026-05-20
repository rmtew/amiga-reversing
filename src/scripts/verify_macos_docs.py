#!/usr/bin/env python3
"""Verify committed Classic Mac OS Markdown reference docs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", type=Path, default=Path("ext/docs_macos"))
    parser.add_argument("--skip-audits", action="store_true")
    parser.add_argument("--update-source-hashes", action="store_true")
    args = parser.parse_args()

    docs = resolve(args.docs)
    errors: list[str] = []

    if not args.skip_audits:
        run_script("src/scripts/audit_macos_docs_against_includes.py")
        run_script("src/scripts/audit_macos_text_quality.py")

    md_docs = sorted(path for path in docs.glob("*.md") if path.name != "README.md")
    if not md_docs:
        errors.append(f"{rel(docs)}: no Markdown docs found")

    errors.extend(check_source_jsons(docs, md_docs, update_hashes=args.update_source_hashes))
    errors.extend(check_zero_audit(docs / "macos_include_audit.json", "macos_doc_include_audit.v1"))
    errors.extend(check_zero_audit(docs / "macos_text_audit.json", "macos_doc_text_audit.v1"))
    errors.extend(check_counted_json(docs / "macos_include_amendments.json", "amendments", "amendment_count"))
    errors.extend(check_counted_json(docs / "macos_text_amendments.json", "amendments", "amendment_count"))
    errors.extend(check_counted_json(docs / "macos_source_amendments.json", "amendments", "amendment_count"))
    errors.extend(check_counted_json(docs / "macos_text_audit_suppressions.json", "suppressions", "suppression_count"))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"verified {len(md_docs)} Mac doc(s)")
    print("include audit finding_count=0")
    print("text audit finding_count=0")
    return 0


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_script(script: str) -> None:
    subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_source_jsons(docs: Path, md_docs: list[Path], *, update_hashes: bool) -> list[str]:
    errors: list[str] = []
    md_names = {path.name for path in md_docs}
    source_jsons = sorted(docs.glob("*.source.json"))
    source_md_names: set[str] = set()

    for source_json in source_jsons:
        data = load_json(source_json)
        paths = data.get("paths", {})
        if not isinstance(paths, dict):
            errors.append(f"{rel(source_json)}: missing paths object")
            continue
        final_md_value = paths.get("final_md")
        if not isinstance(final_md_value, str):
            errors.append(f"{rel(source_json)}: missing paths.final_md")
            continue
        final_md = resolve(Path(final_md_value))
        source_md_names.add(final_md.name)
        if final_md.name not in md_names:
            errors.append(f"{rel(source_json)}: paths.final_md is not a committed Mac doc: {final_md_value}")
            continue
        if not final_md.exists():
            errors.append(f"{rel(source_json)}: missing final_md {final_md_value}")
            continue
        for key in ("source_pdf", "baseline_md"):
            value = paths.get(key)
            if isinstance(value, str) and not resolve(Path(value)).exists():
                errors.append(f"{rel(source_json)}: missing paths.{key} {value}")

        hashes = data.get("sha256", {})
        if not isinstance(hashes, dict):
            errors.append(f"{rel(source_json)}: missing sha256 object")
            continue
        current = sha256(final_md)
        recorded = hashes.get("final_md")
        if recorded != current:
            if update_hashes:
                hashes["final_md"] = current
                write_json(source_json, data)
            else:
                errors.append(f"{rel(source_json)}: stale sha256.final_md")

    missing_sources = sorted(md_names - source_md_names)
    for name in missing_sources:
        errors.append(f"{name}: missing matching .source.json")
    extra_sources = sorted(source_md_names - md_names)
    for name in extra_sources:
        errors.append(f"{name}: source json references non-doc Markdown")
    return errors


def check_zero_audit(path: Path, schema: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{rel(path)}: missing audit report"]
    data = load_json(path)
    if data.get("schema") != schema:
        errors.append(f"{rel(path)}: expected schema {schema}")
    if data.get("finding_count") != 0:
        errors.append(f"{rel(path)}: finding_count={data.get('finding_count')}")
    findings = data.get("findings")
    if findings != []:
        errors.append(f"{rel(path)}: findings not empty")
    return errors


def check_counted_json(path: Path, list_key: str, count_key: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{rel(path)}: missing"]
    data = load_json(path)
    items = data.get(list_key)
    if not isinstance(items, list):
        return [f"{rel(path)}: missing list {list_key}"]
    if data.get(count_key) != len(items):
        errors.append(f"{rel(path)}: {count_key}={data.get(count_key)} but {list_key} has {len(items)}")
    doc_counts = Counter(item.get("document") for item in items if isinstance(item, dict))
    missing_doc = doc_counts.get(None, 0)
    if missing_doc:
        errors.append(f"{rel(path)}: {missing_doc} item(s) missing document")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
