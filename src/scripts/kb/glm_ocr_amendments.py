"""Generate GLM-OCR amendment pages for weak Markdown source pages."""

from __future__ import annotations

import argparse
import base64
import json
import urllib.request
from pathlib import Path
from typing import Any, cast

import fitz  # type: ignore[import-untyped]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run GLM-OCR over weak source pages and store amendments.")
    parser.add_argument("source_json", nargs="+", type=Path)
    parser.add_argument("--endpoint", default="http://127.0.0.1:18080/v1/chat/completions")
    parser.add_argument("--dpi", type=int, default=180)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--review-status", default="seeded")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    for source_json in args.source_json:
        process_source_json(
            source_json,
            endpoint=args.endpoint,
            dpi=args.dpi,
            max_tokens=args.max_tokens,
            review_status=args.review_status,
            force=args.force,
        )
    return 0


def process_source_json(
    source_json: Path,
    *,
    endpoint: str,
    dpi: int,
    max_tokens: int,
    review_status: str,
    force: bool,
) -> None:
    metadata = _load_json(source_json)
    final_md = Path(cast(str, cast(dict[str, object], metadata["paths"])["final_md"]))
    source_pdf = Path(cast(str, cast(dict[str, object], metadata["paths"])["source_pdf"]))
    weak_pages = [int(page) for page in cast(dict[str, list[int]], metadata["remaining_review"])["weak_pages"]]
    amendments_dir = final_md.with_suffix("").with_name(final_md.stem + ".amendments")
    amendments_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(source_pdf)
    amendments = cast(list[dict[str, object]], metadata.setdefault("amendments", []))
    existing_by_page = {
        int(entry["page"]): entry
        for entry in amendments
        if entry.get("method") == "glm-ocr-q8_0" and isinstance(entry.get("page"), int)
    }

    for page_number in weak_pages:
        output = amendments_dir / f"page_{page_number:03d}.glm.md"
        if output.exists() and page_number in existing_by_page and not force:
            print(f"skip existing {output}")
            continue
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"{source_pdf}: page out of range: {page_number}")

        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        png_bytes = pix.tobytes("png")
        text = request_glm_ocr(png_bytes, endpoint=endpoint, max_tokens=max_tokens)
        output.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")
        print(f"wrote {output}")

        entry = {
            "page": page_number,
            "method": "glm-ocr-q8_0",
            "reason": "baseline OCR page has low or empty text",
            "path": output.as_posix(),
            "review_status": review_status,
            "dpi": dpi,
        }
        existing = existing_by_page.get(page_number)
        if existing is None:
            amendments.append(entry)
        else:
            existing.update(entry)

    amendments.sort(key=lambda entry: (int(entry.get("page", 0)), str(entry.get("path", ""))))
    source_json.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def request_glm_ocr(png_bytes: bytes, *, endpoint: str, max_tokens: int) -> str:
    image_data = base64.b64encode(png_bytes).decode("ascii")
    payload = {
        "model": "glm-ocr",
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "OCR markdown. Transcribe the page faithfully. "
                            "Preserve headings, tables, code, punctuation, and line order. "
                            "Do not add commentary."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
                ],
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.loads(response.read().decode("utf-8"))
    return cast(str, result["choices"][0]["message"]["content"])


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
