# PDF To Markdown Source Prep

This project often needs old platform reference books that exist only as PDFs
or scans. The goal is not to make Markdown the final knowledge base. The goal
is to make local source material searchable, page-cited, reviewable, and good
enough to support structured KB extraction.

The end state for each document is:

```text
source PDF or OCR PDF
  -> baseline page-cited Markdown
  -> selected page repairs
  -> final page-cited Markdown
  -> per-document metadata JSON
  -> source inventory row
  -> cited KB facts, corrections, or parser assertions
```

Markdown is a source-prep artifact. Structured JSON KB files still own facts.

## Quick Start

For a text-layer PDF:

```powershell
uv run python src\scripts\kb\pdf_to_markdown.py `
  resources\platform_atari_st\docs\SomeBook.pdf `
  --probe

uv run python src\scripts\kb\pdf_to_markdown.py `
  resources\platform_atari_st\docs\SomeBook.pdf `
  -o resources\platform_atari_st\docs\SomeBook.baseline.md
```

For an image-only scan, OCR it first:

```bash
sudo apt update
sudo apt install ocrmypdf tesseract-ocr
cd /mnt/c/Data/R/git/claude-repos/amiga-reversing2

ocrmypdf --deskew --rotate-pages \
  resources/platform_atari_st/docs/SomeBook.pdf \
  resources/platform_atari_st/docs/SomeBook.ocr.pdf
```

Then convert the OCR PDF:

```powershell
uv run python src\scripts\kb\pdf_to_markdown.py `
  resources\platform_atari_st\docs\SomeBook.ocr.pdf `
  -o resources\platform_atari_st\docs\SomeBook.baseline.md
```

## Why This Exists

The M68K parser currently reads the Motorola PDF directly with PyMuPDF and then
does a lot of PDF-layout recovery. That is appropriate for highly formal
instruction data where generated tools need exact fields.

Atari ST books are different. They are weaker sources, often scans, and usually
contain a mix of prose, examples, tables, and indexes. For those, a better first
step is:

```text
make source text stable
make citations cheap
make weak pages visible
parse only targeted sections later
```

This keeps parser work driven by actual KB needs instead of by PDF layout noise.

## Artifact Layout

Use one stem per document. Local source PDFs and OCR PDFs stay in
`resources/`. Final committed Markdown and metadata live in `ext/docs_atari_st/`.

```text
resources/platform_atari_st/docs/
  SomeBook.pdf
  SomeBook.ocr.pdf                  optional local OCR derivative
  SomeBook.baseline.md              raw OCR/text-layer Markdown

ext/docs_atari_st/
  SomeBook.md                       final reviewed Markdown
  SomeBook.source.json              metadata and review state
  SomeBook.amendments/
    page_004.glm.md
    page_042.glm.md
    page_042.reviewed.md
```

If a document already has a good text layer, `SomeBook.ocr.pdf` is not needed.

`SomeBook.baseline.md` is the direct output of `pdf_to_markdown.py`.
`ext/docs_atari_st/SomeBook.md` is the source we cite from KB work. It may be
identical to the baseline or may include reviewed repairs.

## Baseline Markdown

Every converted page must keep source-page markers:

```md
<!-- source-pdf: resources/platform_atari_st/docs/SomeBook.ocr.pdf -->
<!-- source-pages: 356 -->

<!-- source-page: 42 -->
## Page 42

Page text here...
```

These markers are the citation contract. KB entries should cite page numbers,
not fragile Markdown line numbers.

Example citation:

```json
{
  "source_id": "compute-vdi-vol1-md",
  "citation": {
    "path": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md",
    "page": 42
  }
}
```

## OCRmyPDF Baseline

OCRmyPDF is the baseline OCR path because it is deterministic, widely used, and
produces searchable PDFs that other tools can consume.

Recommended command:

```bash
ocrmypdf --deskew --rotate-pages input.pdf output.ocr.pdf
```

`--deskew` straightens tilted scan pages.

`--rotate-pages` fixes sideways or upside-down pages where detected.

After OCR, probe the result:

```powershell
uv run python src\scripts\kb\pdf_to_markdown.py output.ocr.pdf --probe
```

The probe reports:

```json
{
  "page_count": 356,
  "text_pages": 341,
  "empty_text_pages": 15,
  "low_text_pages": [5, 7, 9],
  "image_blocks": 356,
  "needs_ocr": false
}
```

Use this report to seed the document metadata.

## GLM-OCR Repairs

GLM-OCR through `llama.cpp` is useful as a second-pass repair tool. It should
not silently replace the baseline for every page.

Good GLM-OCR uses:

```text
contents and indexes
weak OCR pages
blank OCR pages
prose with bad line-break hyphenation
some tables after review
```

Risky GLM-OCR uses:

```text
code listings
register names
opcodes
symbol names
small numeric fields
anything where 0/O, 1/l/I, or punctuation matters
```

In tests, GLM-OCR produced cleaner prose and contents pages than OCRmyPDF, but
it could normalize ambiguous code glyphs incorrectly. For example, a code page
may become more readable while changing `contrl0` into `contr10` or `.l` into
`.1`. Treat those pages as seeded until image-reviewed.

### Running The Local Server

If `llama-server` can download from Hugging Face directly:

```powershell
llama-server -hf ggml-org/GLM-OCR-GGUF:Q8_0 `
  --port 18080 `
  --host 127.0.0.1 `
  --temp 0.1 `
  --top-k 1 `
  --ctx-size 4096 `
  --no-webui
```

If the built-in downloader fails, download the files with `curl`:

```powershell
curl.exe -L -C - `
  -o tmp\glm_ocr\GLM-OCR-Q8_0.gguf `
  https://huggingface.co/ggml-org/GLM-OCR-GGUF/resolve/main/GLM-OCR-Q8_0.gguf

curl.exe -L -C - `
  -o tmp\glm_ocr\mmproj-GLM-OCR-Q8_0.gguf `
  https://huggingface.co/ggml-org/GLM-OCR-GGUF/resolve/main/mmproj-GLM-OCR-Q8_0.gguf
```

Then run from local files:

```powershell
llama-server `
  -m tmp\glm_ocr\GLM-OCR-Q8_0.gguf `
  --mmproj tmp\glm_ocr\mmproj-GLM-OCR-Q8_0.gguf `
  --port 18080 `
  --host 127.0.0.1 `
  --temp 0.1 `
  --top-k 1 `
  --ctx-size 4096 `
  --no-webui
```

### Rendering Pages

Render selected pages from the original PDF, not from already-OCRed text:

```powershell
uv run python -c "import fitz; p='resources/platform_atari_st/docs/SomeBook.pdf'; d=fitz.open(p); page=d[41]; pix=page.get_pixmap(dpi=180, alpha=False); pix.save('tmp/glm_ocr/SomeBook_page_042.png')"
```

Page indexes are zero-based in PyMuPDF. `d[41]` renders source page 42.

### Calling The Server

Send a data URL image to the OpenAI-compatible endpoint:

```powershell
$image = 'tmp\glm_ocr\SomeBook_page_042.png'
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($image))

$body = @{
  model = 'glm-ocr'
  temperature = 0.1
  max_tokens = 2048
  messages = @(
    @{
      role = 'user'
      content = @(
        @{
          type = 'text'
          text = 'OCR markdown. Transcribe the page faithfully. Do not add commentary.'
        },
        @{
          type = 'image_url'
          image_url = @{
            url = "data:image/png;base64,$b64"
          }
        }
      )
    }
  )
} | ConvertTo-Json -Depth 8 -Compress

$response = Invoke-RestMethod `
  -Uri 'http://127.0.0.1:18080/v1/chat/completions' `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body `
  -TimeoutSec 300

$response.choices[0].message.content |
  Set-Content resources\platform_atari_st\docs\SomeBook.amendments\page_042.glm.md -Encoding UTF8
```

## Metadata JSON

Each final document should have a metadata file:

```json
{
  "schema_version": 1,
  "source_id": "compute-vdi-vol1-md",
  "title": "COMPUTE!'s Technical Reference Guide: Atari ST Volume One: VDI",
  "publisher": "COMPUTE! Publications",
  "year": 1987,
  "domain": ["atari-st", "vdi", "gem"],
  "paths": {
    "source_pdf": "resources/platform_atari_st/docs/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.pdf",
    "ocr_pdf": "resources/platform_atari_st/docs/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.ocr.pdf",
    "baseline_md": "resources/platform_atari_st/docs/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.baseline.md",
    "final_md": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md"
  },
  "source_sha256": {
    "source_pdf": null,
    "ocr_pdf": null,
    "baseline_md": null,
    "final_md": null
  },
  "conversion": {
    "ocr_tool": "ocrmypdf",
    "ocr_options": ["--deskew", "--rotate-pages"],
    "markdown_tool": "src/scripts/kb/pdf_to_markdown.py"
  },
  "probe": {
    "page_count": 356,
    "text_pages": 341,
    "empty_text_pages": 15,
    "low_text_pages": [5, 7, 9]
  },
  "amendments": [
    {
      "page": 42,
      "method": "glm-ocr-q8_0",
      "reason": "baseline OCR has code/table noise",
      "path": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.amendments/page_042.glm.md",
      "review_status": "seeded"
    }
  ],
  "remaining_review": {
    "weak_pages": [5, 7, 9],
    "code_or_symbol_pages": [42]
  },
  "usage": {
    "citation_quality": "page",
    "machine_readable": true,
    "decision": "cite_manually"
  }
}
```

Review statuses:

```text
seeded
  generated repair exists but has not been image-checked

validated
  repair was checked against page image and accepted

rejected
  repair was tried but should not be used
```

## Final Markdown Assembly

The final Markdown should be produced mechanically from:

```text
baseline Markdown
  + validated amendments
  + optional manually reviewed page replacements
```

Do not edit large generated Markdown files ad hoc if a page replacement file
would make the change auditable.

Conceptual assembly:

```text
for each source page:
  if validated replacement exists:
    write original source-page marker
    write replacement page text
  else:
    write baseline page text
```

The source-page marker must remain stable even when the page body is replaced.

## Source Inventory

Each final Markdown source should have a source inventory row. For Atari ST this
belongs in the Atari platform source inventory proposed in
`docs/proposals/011-atari-st-platform-knowledge.md`.

Example:

```json
{
  "id": "compute-vdi-vol1-md",
  "title": "COMPUTE!'s Technical Reference Guide: Atari ST Volume One: VDI",
  "publisher": "COMPUTE! Publications",
  "domain": ["vdi", "gem", "graphics"],
  "tier": 3,
  "path": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md",
  "url": null,
  "availability": "optional_local",
  "machine_readable": true,
  "citation_quality": "page",
  "parser_feasibility": "targeted",
  "extraction_status": "candidate",
  "review_status": "seeded",
  "decision": "cite_manually",
  "license_notes": "User-supplied local reference. Do not require redistribution.",
  "known_conflicts": []
}
```

## Using Markdown As A Cited Reference

Markdown can support:

```text
cited corrections
parser assertions
manual candidate facts
targeted parser extraction
review notes for future structured KB work
```

Markdown should not become:

```text
runtime metadata
the only owner of a platform fact
an uncited source for generated C tables
```

Good KB fact shape:

```json
{
  "family": "VDI",
  "opcode": 3,
  "symbol_name": "v_clrwk",
  "source_id": "compute-vdi-vol1-md",
  "citation": {
    "path": "ext/docs_atari_st/Computes_Technical_Ref_Guide_Atari_ST_Vol_one.md",
    "page": 42
  },
  "review_status": "seeded"
}
```

Before a fact is promoted to validated, check xrefs or another source where
practical, especially for opcodes, names, calling conventions, and register
fields.

## Quality Checklist

Before treating a document as usable:

- Probe output exists and page count matches the PDF.
- Final Markdown has page markers for all non-empty pages.
- Empty and low-text pages are listed in metadata.
- GLM repairs are stored as amendments, not silently overwritten.
- Code/symbol/opcode pages are manually reviewed before validation.
- Search finds expected domain terms.
- Source inventory row exists or is planned.
- KB facts cite `source_id` plus page.

Useful searches:

```powershell
Select-String -Path ext\docs_atari_st\SomeBook.md `
  -Pattern "GEMDOS|BIOS|XBIOS|VDI|AES|trap|opcode" `
  -CaseSensitive:$false
```

## Practical Policy

For old commercial books, keep full PDFs and full-book Markdown as local
user-supplied resources unless redistribution is explicitly acceptable. Commit
the tooling, metadata schemas, inventories, and structured KB facts. Do not make
ordinary checks depend on downloading or redistributing the original books.

If the local Markdown is good enough and has metadata, the project can use it as
the normal cited reference. The original PDF is then needed only for future OCR
or image-backed review.
