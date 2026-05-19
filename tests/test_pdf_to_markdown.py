from pathlib import Path

import fitz
import pytest

from src.scripts.kb.pdf_to_markdown import (
    OcrRequiredError,
    parse_pages,
    pdf_to_markdown,
    probe_pdf,
)


def test_probe_pdf_detects_image_only_pdf_needs_ocr(tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    doc = fitz.open()
    doc.new_page(width=100, height=100)
    doc.save(pdf)

    probe = probe_pdf(pdf)

    assert probe.page_count == 1
    assert probe.text_pages == 0
    assert probe.empty_text_pages == 1
    assert probe.needs_ocr is True
    with pytest.raises(OcrRequiredError):
        pdf_to_markdown(pdf)


def test_pdf_to_markdown_preserves_page_provenance(tmp_path: Path) -> None:
    pdf = tmp_path / "text.pdf"
    doc = fitz.open()
    page = doc.new_page(width=300, height=300)
    page.insert_text((36, 36), "Atari ST Reference\nGEMDOS call table")
    doc.save(pdf)

    markdown = pdf_to_markdown(pdf)

    assert f"<!-- source-pdf: {pdf.as_posix()} -->" in markdown
    assert "<!-- source-page: 1 -->" in markdown
    assert "## Page 1" in markdown
    assert "Atari ST Reference" in markdown
    assert "GEMDOS call table" in markdown


def test_parse_pages_accepts_ranges_and_deduplicates() -> None:
    assert parse_pages("1,3-5,4") == [1, 3, 4, 5]

    with pytest.raises(ValueError, match="invalid page range"):
        parse_pages("5-3")
