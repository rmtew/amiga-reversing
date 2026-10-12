# Binary source package directive conformance

## Scope and evidence

The emitted core is `INCBIN "assets/name.bin"`: one whole, deterministic file,
with case-preserved forward-slash relative paths. Range operands are unnecessary
because the exporter writes the exact slice. Labels, expressions, sections and
padding stay in assembly source. A file inclusion is never evidence that its
contents are free of code, pointers or relocations.

Actual oracle checks below used **vasm 2.0e**, Motorola syntax **3.19d**, M68k
backend **2.8**, built locally at `ext/vasm/vasmm68k_mot`. The checks use synthetic
data only. `-devpac` means vasm's compatibility mode, **not real Devpac**.
`bin/GenAm` and `vamos` were unavailable in this checkout/PATH; neither proprietary
tools nor target data were downloaded. GenAm 3.18 execution remains unverified.
The repository's historical GenAm instruction results do not prove these directives.

Primary documentation consulted:

* [vasm Motorola syntax manual](https://sun.hasenbraten.de/vasm/release/vasm_4.html),
  `incbin`, `include`, `incdir`, `-align`, `-devpac`, `even`, `cnop` and `section`.
  The matching distributed documentation is available locally in
  `ext/vasm/doc/syntax_mot.texi`; the web endpoint failed to fetch during research.
* [HiSoft Devpac 3 for Atari ST/STE/TT/Falcon030](https://info-coach.fr/atari/software/_development/Devpac_v3_Manual_txt.pdf#page=70),
  1992, printed pages 67–68 (PDF pages 69–70): inclusion and search rules.
  This is an original publisher manual hosted by an archive, but it is **not**
  the Amiga GenAm 3.18 manual.

A [Devpac Amiga 2 transcription](https://www.scribd.com/document/185730421/Devpac-2-Part-1)
describes start alignment plus odd-length trailing padding. Its introduction
explicitly says it was converted from an ST transcription, so this is historical
corroboration, not authoritative evidence for Amiga GenAm 3.18. It conflicts with
the Atari Devpac 3 manual, which specifies start alignment without end padding.
The [German Amiga manual scan](https://www.retrozone.ch/docs/amiga/HiSoftDevpac.pdf)
was located, but retrieval failed; its contents are not used as evidence here.

## Measured matrix

`blob.bin` contains bytes `00 01 02 03 04`. Unless noted, results are measured
with the actual vasm executable, not inferred from its implementation.

| Input or condition | vasm default | vasm `-devpac` | Devpac evidence / package decision |
| --- | --- | --- | --- |
| `INCBIN "blob.bin"` | Exact whole file | Exact whole file | Whole filename is documented by Devpac 3 |
| Mixed-case `InCbIn` | Accepted | Accepted | Emit canonical spelling |
| Single/double quotes, space/comma inside filename | Both accepted | Both accepted | Emit simple double-quoted names |
| Nested relative asset path | Accepted | Accepted | Use package-relative forward slashes |
| INCBIN after one `DC.B`, odd-sized asset | No start/end padding | No start/end padding | Conflicts with documented Devpac alignment; do not claim equivalence |
| Empty file | Zero bytes | Zero bytes | Exporter need not create empty assets |
| `INCBIN "blob.bin",2` | `02 03 04` | Syntax error | Optional offsets are outside portable core |
| `INCBIN "blob.bin",1,2` | `01 02` | Syntax error | Optional lengths are outside portable core |
| Length beyond EOF: `,3,9` | Clipped to `03 04` | Syntax error | A manifest hash/length must detect truncation before assembly |
| Offset exactly EOF: `,5` | Zero bytes | Syntax error | Not emitted |
| Offset negative or beyond EOF | Error: bad file-offset | Syntax error | Reject, never silently pad |
| Length zero: `,0,0` | Entire file | Syntax error | Zero does **not** mean zero output in this oracle |
| Negative length: `,1,-1` | Entire remainder | Syntax error | Observed extension, not a portable contract |
| Extra operand: `,1,2,3` | Extra operand ignored, emits `01 02` | Syntax error | Internal parser may reject more strictly; not emitted |
| Missing file | Fatal open error | Fatal open error | Package validation must fail closed |
| Nested source INCLUDE with `incbin "blob.bin"` | CWD file wins over included source directory and `-I` directory | Same documented search model; default-mode shadow case tested | Stage package and set CWD explicitly |
| Odd asset then `DC.W $1234` | Word emitted immediately | Zero pad inserted before word | Preserve profile alignment; do not insert/remove guessed padding |
| Odd asset then `EVEN; DC.W $1234` | One zero pad | One zero pad | Explicit source layout |
| Odd asset then `DS.B 1; DC.W $1234` | One zero pad | Not separately measured | Preserve reserve directives |
| Two assets, labels, `DC.L other_section_label`, label difference, CODE/DATA/BSS | Full hunk executable equals inline-byte version | Full hunk executable equals inline-byte version | Relocations and sections remain source-owned |

The Atari Devpac 3 manual describes INCLUDE search relative to the main source,
additional include directories, nested includes, quoted space-containing names,
and preassembled `.GS` files. It says INCBIN uses the same lookup mechanism. Do not
assume those host/path rules equal vasm's working-directory-first lookup. Generated
packages bundle literal SDK source INCLUDE dependencies; they do not require
`.GS`, INCDIR, drive prefixes, host absolute paths, traversal, escapes or range expressions. The internal package resolver is
intentionally constrained to the package root; broad assembler filesystem access
is not a compatibility requirement.

## Contract and remaining limits

Binary packages currently target the vasm profile; an unverified Devpac package
must be refused rather than advertised as GenAm-compatible. Ordinary source-only
Devpac export remains supported. Even-address, even-length assets avoid the known
historical alignment differences, but that alone does not certify GenAm 3.18.

The source parser need only implement the emitted whole-file core initially.
Unsupported optional syntax must fail explicitly. Future offset/length support
requires profile-specific grammar and tests for EOF clipping and zero length;
Python slicing alone does not match measured vasm semantics.

Complete-package verification must read staged files from one explicit root, check
their manifest lengths and hashes, and compare complete rebuilt binaries. A source
text digest cannot establish package identity. INCLUDE search must never pick a
same-named unrelated asset from the repository or process working directory.

Before claiming real GenAm 3.18 compatibility, provide an authorized local GenAm
binary and working vamos environment, then run the same whole-file fixtures with
start/end oddness, empty files, quotation, missing files, nested paths, alignment,
sections and relocations. Compare full Amiga hunk output (GenAm does not supply the
same raw-output mode), account for documented container differences explicitly,
and record version, options and exact output hashes. No vasm compatibility flag
can substitute for this missing oracle.

## Reproduce

```sh
make -C ext/vasm CPU=m68k SYNTAX=mot
VASM="$PWD/ext/vasm/vasmm68k_mot" .venv/bin/python -m pytest -q tests/test_incbin_oracle_conformance.py
```

Result in the implementation environment: **22 passed**, including two full-hunk
comparisons (default and `-devpac`). Fixtures and outputs live in pytest temporary
directories. If a native vasm is unavailable these tests skip with a specific
reason; they never download an assembler. These are oracle characterization tests;
the internal assembler and exported-package integration suites provide the
separate cross-assembler correctness checks.
