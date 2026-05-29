# Amiga Reversing Toolkit

Spec-driven toolchain for reverse engineering Amiga 68000 binaries. All M68K
knowledge is extracted from the Motorola Programmer's Reference Manual PDF into
structured JSON, then used to generate a disassembler, assembler, symbolic
executor, and effect predictor. External oracles (vasm, Musashi) verify the
generated tools -- they are never part of the toolchain itself.

## Structure

```
src/            C disassembler, assembler, analysis, disk/file CLIs, generated metadata
amiga_reversing/ Python web/API/project orchestration, DTO adapters, and runtime CLI tools
tests/          Python web/orchestration pytest suite
knowledge/      Generated JSON knowledge bases (M68K ISA, Amiga HW, OS)
ext/vasm/       Vendored vasm assembler source
targets/        Per-target projects, generated source, review state, and reports
bin/            User-supplied target binaries
resources/      External reference files (not tracked, see RESOURCES.md)
```

## Setup

```
py -m venv .venv
.venv\Scripts\activate
uv sync --dev
ext\vasm\build.bat                       # build vasm (requires MSVC)
```

External resources (M68K PDF, NDK 3.1, Hardware Manual) must be obtained
separately. See [RESOURCES.md](RESOURCES.md) for details.

## Example: disassembling GenAm

```
# Generate disassembly
uv run amiga-gen-disasm bin/GenAm -t targets/amiga_hunk_genam

# Run tests
py -m pytest
```

## Knowledge base rebuild

If you have the source documents, regenerate the JSON knowledge bases with
maintenance scripts under `src.scripts`:

```
uv run python -m src.scripts.kb.m68k_parser resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf
uv run python -m src.scripts.parse_hw_manual resources/Hardware_Manual.html
uv run python -m src.scripts.kb.ndk_parser /path/to/NDK_3.1
```

Classic Mac OS source inventory checks use the committed
`knowledge/macos_source_inventory.json` metadata:

```
uv run macos-platform-kb report
uv run macos-platform-kb check
```

## PDF OCR prep

For scanned platform reference PDFs, add a searchable text layer before
Markdown/source extraction. On Windows, the most reliable path is OCRmyPDF
inside WSL:

```bash
sudo apt update
sudo apt install ocrmypdf tesseract-ocr
cd /mnt/c/Data/R/git/claude-repos/amiga-reversing2
ocrmypdf --deskew --rotate-pages input.pdf output.ocr.pdf
```

Then convert text-layer PDFs to page-cited Markdown:

```powershell
uv run python src\scripts\kb\pdf_to_markdown.py output.ocr.pdf -o output.md
```

Use `--probe` first to detect image-only PDFs or weak OCR coverage.

## Validation

Run the normal Python/web checks:

```
uv run pytest -q
```

Run the generated C toolchain validation:

```
cmd /c src\precommit.bat
```

Check committed rendered source by rebuilding every imported target with an
`asm.s` file:

```
uv run platform-rendered-source-roundtrip
```

Current output starts with a summary, then one row per target:

```
Rendered source round-trip: 25/36 full-file exact, 10 content-exact only, 1 unsupported, 0 failures
full-file-exact    amiga_disk_carrier-command-1994-kixx-budget__amiga_raw_bootblock
full-file-exact    amiga_disk_conqueror-1990-rainbow-arts-de-en__amiga_hunk_conqueror_cf971606
content-exact-only amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_menu_252a2566 (size_mismatch, container_shape_mismatch)
unsupported        macos_hfs_mpw_gm__macos_file_mpw_tools_asm (unsupported_platform_source_assembly)
```

`full-file-exact` means rendered source rebuilt the original file/container
byte-for-byte. `content-exact-only` means the useful payload/relocation content
matches, but the container shape is not reproduced exactly. The command always
assembles the tracked `asm.s` text and compares the deterministic report at
`docs/validation/rendered-source-roundtrip-report.json`. If the report drifts,
the command rewrites that file, prints `report-drift`, and exits non-zero so the
diff can be reviewed. `--update-rendered-source` rewrites supported targets from
the current renderer first, then verifies that same text and refreshes the
report intentionally. `unsupported` is reported explicitly for rendered source
that exists but cannot currently be assembled, such as Mac OS `asm.s`.

See [docs/reproduction.md](docs/reproduction.md) for the web UI binary
reproduction workflow and assembler customization policy.
