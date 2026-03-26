# Amiga Reversing Toolkit

Spec-driven toolchain for reverse engineering Amiga 68000 binaries. All M68K
knowledge is extracted from the Motorola Programmer's Reference Manual PDF into
structured JSON, then used to generate a disassembler, assembler, symbolic
executor, and effect predictor. External oracles (vasm, Musashi) verify the
generated tools -- they are never part of the toolchain itself.

## Structure

```
m68k/           Python package: disassembler, assembler, executor, analysis
scripts/        CLI tools: parsers, pipeline scripts, oracle harnesses
tests/          pytest suite (py -m pytest)
knowledge/      Generated JSON knowledge bases (M68K ISA, Amiga HW, OS)
ext/vasm/       Vendored vasm assembler source
targets/        Per-target output (entities, disassembly, progress)
bin/            User-supplied target binaries
resources/      External reference files (not tracked, see RESOURCES.md)
```

## Setup

```
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt    # if present
ext\vasm\build.bat                       # build vasm (requires MSVC)
```

External resources (M68K PDF, NDK 3.1, Hardware Manual) must be obtained
separately. See [RESOURCES.md](RESOURCES.md) for details.

## Example: disassembling GenAm

```
# Build entity database
py scripts/build_entities.py bin/GenAm -t targets/amiga_hunk_genam

# Generate disassembly
py scripts/gen_disasm.py bin/GenAm -t targets/amiga_hunk_genam

# Update progress dashboard
py scripts/update_progress.py -t targets/amiga_hunk_genam

# Run tests
py -m pytest
```

## Knowledge base rebuild

If you have the source documents, regenerate the JSON knowledge bases:

```
py scripts/parse_m68k.py resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf
py scripts/parse_hw_manual.py resources/Hardware_Manual.html
py scripts/parse_ndk.py /path/to/NDK_3.1
```

## Oracle tests

These require external tools (vasm, machine68k) and are run separately from
the pytest suite:

```
py scripts/oracle_m68k_asm.py vasm
py scripts/oracle_m68k_exec.py
```
