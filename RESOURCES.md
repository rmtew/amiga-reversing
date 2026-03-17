# External Resources

This project depends on several external files that are not included in the
repository due to copyright or size. Place them in `resources/` as described
below.

## M68K Programmer's Reference Manual (required)

- **File:** `resources/M68000PM_AD_Rev_1_Programmers_Reference_Manual_1992.pdf`
- **Used by:** `scripts/parse_m68k.py` (extracts instruction encodings, EA modes,
  constraints into `knowledge/m68k_instructions.json`)
- **Source:** Motorola M68000 Family Programmer's Reference Manual (1992).
  Freely available from various archive sites; search for the title.

## Amiga Hardware Manual HTML (required)

- **Files:** `resources/Hardware_Manual.html` and `resources/Hardware_Manual_guide/`
  (764 HTML files)
- **Used by:** `scripts/parse_hw_manual.py` (extracts register definitions into
  `knowledge/amiga_hw_registers.json`)
- **Source:** Amiga Hardware Reference Manual, AmigaGuide-to-HTML conversion.
  Available on the ADCD 2.1 disc or amiga-dev.wikidot.com.

## NDK 3.1 (required)

- **Directory:** Available at any path; configure in parser invocation
- **Used by:** `scripts/parse_ndk.py` (extracts OS function signatures, structs,
  constants into `knowledge/amiga_os_reference.json`)
- **Contents needed:** FD files, autodocs, and include files (especially `.i` asm
  headers for struct/constant definitions)
- **Source:** Commodore/Hyperion NDK 3.1. Available on the ADCD 2.1 disc
  (`D:/NDK/NDK_3.1`) or from Hyperion Entertainment.

## Game binaries (per-game)

- **Directory:** `bin/`
- **Used by:** `scripts/build_entities.py`, `scripts/gen_disasm.py`
- **Source:** User-supplied. Amiga hunk-format executables to disassemble.

## Target binaries for analysis (optional)

- **Example:** `resources/Amiga_Devpac_3_18/GenAm` (DevPac 3.18 assembler)
- **Used by:** Analysis pipeline as a test target
- **Source:** DevPac 3.18 distribution (commercial software)

## amitools / machine68k (optional, for oracle testing)

- **Install:** `uv tool install "./resources/amitools[vamos]" --with "machine68k"`
- **Source:** Clone from GitHub into `resources/amitools/` and `resources/machine68k/`
  - https://github.com/cnvogelg/amitools
  - https://github.com/cnvogelg/machine68k
- **Note:** machine68k needs a Windows path fix (`os.path.normpath()` on subprocess
  exe path) for `CreateProcess` compatibility.

## vasm (included)

The vasm assembler source is vendored in `ext/vasm/` (open source, free for
non-commercial use). Build with:

```
ext\vasm\build.bat        # Windows (requires MSVC cl.exe in PATH)
```

This produces `tools/vasmm68k_mot.exe`, used for round-trip verification.

- **Source:** http://sun.hasenbraten.de/vasm/
- **License:** Free for non-commercial use
