"""Apply validated page amendments to page-cited Markdown sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

PAGE_SPLIT_RE = re.compile(r"(<!-- source-page: (\d+) -->\n## Page \2\n\n)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply validated amendments to final page-cited Markdown.")
    parser.add_argument("source_json", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    for source_json in args.source_json:
        apply_source(source_json, dry_run=args.dry_run)
    return 0


def apply_source(source_json: Path, *, dry_run: bool = False) -> None:
    metadata = _load_json(source_json)
    final_md = Path(cast(str, cast(dict[str, object], metadata["paths"])["final_md"]))
    amendments = [
        entry
        for entry in cast(list[dict[str, object]], metadata.get("amendments", []))
        if entry.get("review_status") == "validated"
    ]
    replacements = {
        int(entry["page"]): Path(cast(str, entry["path"])).read_text(encoding="utf-8").strip()
        for entry in amendments
    }

    original = final_md.read_text(encoding="utf-8")
    rebuilt, applied = apply_replacements(original, replacements)
    print(f"{final_md}: validated={len(replacements)} applied={len(applied)}")
    if dry_run:
        return
    if rebuilt != original:
        final_md.write_text(rebuilt, encoding="utf-8", newline="\n")
    metadata["applied_amendments"] = {
        "tool": "src/scripts/kb/apply_pdf_md_amendments.py",
        "pages": applied,
        "final_md_sha256_after": _sha256(final_md),
    }
    cast(dict[str, object], metadata["sha256"])["final_md"] = metadata["applied_amendments"][
        "final_md_sha256_after"
    ]
    source_json.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def apply_replacements(markdown: str, replacements: dict[int, str]) -> tuple[str, list[int]]:
    parts = PAGE_SPLIT_RE.split(markdown)
    if len(parts) == 1:
        raise ValueError("markdown has no source-page markers")

    output = [parts[0].rstrip(), ""]
    applied: list[int] = []
    index = 1
    while index < len(parts):
        marker = parts[index]
        page = int(parts[index + 1])
        body = parts[index + 2]
        replacement = replacements.get(page)
        output.append(marker.rstrip())
        output.append("")
        if replacement is None:
            output.append(body.strip())
        else:
            output.append(replacement)
            applied.append(page)
        output.append("")
        index += 3
    for page in sorted(set(replacements) - set(applied)):
        output.append(f"<!-- source-page: {page} -->")
        output.append(f"## Page {page}")
        output.append("")
        output.append(replacements[page])
        output.append("")
        applied.append(page)
    return "\n".join(output).rstrip() + "\n", applied


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
