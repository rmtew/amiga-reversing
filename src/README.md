# C99 Assembler Scaffold

Isolated C-side generator, corpus, and tests live under `src/`.

## Commands

Generate the C subset tables:

```powershell
uv run python src/scripts/generate_c99_assembler_subset.py --output-dir src
```

Generate the oracle corpus files:

```powershell
uv run python src/scripts/generate_c99_assembler_corpus.py --output-dir src/tests/generated
```

Build the C subset tools with MSVC:

```powershell
src\build.bat
```

Run corpus verification with the built C tool:

```powershell
src\build.bat verify-corpus
```

```powershell
src\build.bat verify-manifest src\tests\generated\full_ext_cases.txt
```

Assemble one generated corpus case to stdout:

```powershell
src\build.bat assemble-case src\tests\generated\all_cases.txt bra_b_sample
```

Assemble the full generated manifest to a binary:

```powershell
src\build.bat assemble-manifest src\tests\generated\all_cases.txt src\tests\generated\all_cases.rebuilt.bin
```

Assemble one line of supported source text:

```powershell
src\build.bat assemble-line "clr.b d0"
```

Assemble a simple source file to binary:

```powershell
src\build.bat assemble-file input.s out.bin
```

`assemble-line` currently supports the generated subset and numeric branch displacements.

`assemble-file` now supports file-level labels with two-pass branch resolution for the generated subset.

Indexed EA text also supports internal full-extension options like:

```powershell
lea.l $10(a0,d1.w){full,bdw=$1234,odw=$5678,iis=3},a0
```

Run the isolated `unittest` suite:

```powershell
uv run python -m unittest discover -s src/tests -p "test_*.py"
```

Run lint on the isolated Python support files:

```powershell
uv run ruff check src/scripts/generate_c99_assembler_subset.py src/scripts/generate_c99_assembler_corpus.py src/tests/test_c99_assembler_codegen.py src/tests/test_c99_assembler_corpus.py
```

## Generated Files

Corpus output:

- `src/tests/generated/all_cases.s`
- `src/tests/generated/all_cases.json`
- `src/tests/generated/all_cases.txt` — generic encoded instruction-sequence verifier manifest
- `src/tests/generated/all_cases.bin`
- `src/tests/generated/full_ext_cases.txt`

C subset output:

- `src/m68k_asm_tables.h`
- `src/m68k_asm_tables.c`
- `src/m68k_disassembler_tables.inc`

Static runtime:

- `src/m68k_assembler.h`
- `src/m68k_assembler.c`
- `src/m68k_disassembler.h`
- `src/m68k_disassembler.c`
