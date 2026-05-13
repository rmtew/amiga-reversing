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

## Validation

Run the normal Python/web checks:

```
uv run pytest -q
```

Run the generated C toolchain validation:

```
cmd /c src\precommit.bat
```

See [docs/reproduction.md](docs/reproduction.md) for the web UI binary
reproduction workflow and assembler customization policy.
