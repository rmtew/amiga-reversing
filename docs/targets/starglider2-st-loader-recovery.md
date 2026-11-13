# Starglider II ST loader recovery

The supplied STX yields a source-mapped main load. Its decoded header says
`StarGlider 2`, `Ver 1.05 1st September 1988.` and `Release Version.` This
identifies the recovered content, not the authenticity of the disk's filename.
The Amiga restoration remains paused. No supplied media or recovered binary is
committed by this milestone.

## Reproduce

Build the native tools, then run the committed recipe with private paths:

```sh
make -j4 all
python -m amiga_reversing.tools.recover_stx \
  --image '/private/Starglider 2 (1988)(Rainbird).zip' \
  --plan targets/atari_st_starglider2_stx/recovery_plan.json \
  --output-dir /private/sgii-st-recovered
```

Use a new or empty output directory. The command checks the input identity,
selects exact physical sectors through the native STX reader, runs bounded
slices of the original decoder instructions, and checks every captured output.
It writes six binaries and `recovery.json`. The report maps each assembled
extent to its STX file offset, physical track/sector instance and exact CHRN.
It also records recipe identity, CPU stop points and artifact identities. This
is a recovery recipe, not a second target-analysis database or a rendered source
project. Linked release/target integration is the next milestone.

## Successful loader path

1. The 512-byte boot sector branches to offset `$2C`. It copies 128 LONGs from
   offset `$58` to `$77800`, XORing each LONG with a counter from 127 downwards.
   Only 424 source bytes are in the boot sector. The remaining 88 source bytes
   are **not** assumed to be the next disk sector or invented as zeroes. The
   recipe executes setup plus 106 complete copy iterations and retains only
   the 424-byte known prefix. It uses `$70000` as an analysis-only location for
   the PC-relative boot buffer, not as a claim about TOS's actual buffer address.
2. The known prefix restores the head, selects drive A/side 0 through PSG port A
   value 5, sets the FDC track register to `$F7`, and makes two STEP IN commands
   (`$40`, without updating that register). It reads physical cylinder 2/side 0,
   sector IDs `$F5`–`$FA`, into `$1000`. The first five DMA counts are two
   512-byte units; the last is one. The recorded CHRN values are `$F7,$F7,R,N`,
   with N `$F7` or `$F6`. STX uses N's low two bits for 1024/512-byte storage;
   the full ID bytes remain intact. Rejecting those upper size bits was an
   over-restrictive reader guard and is now corrected.
3. Those six sectors contain 5,632 bytes. The prefix XORs the first 1,281 LONGs
   with `$12345678`, then transfers to `$1000`. That block copies 512 bytes from
   its offset `$1E` to `$77C00` and jumps to `$77C04`. The helper has four decode
   passes: subtract a descending BYTE counter from `$1E1`; XOR a descending BYTE
   counter from `$1D3`; rotate 450 BYTEs left by three; invert 404 BYTEs. All end
   at helper offset `$1F4`. These are executed by the native CPU, not duplicated
   as Python arithmetic. The decoded WORD at `$77DF2` is `$004B` (75).
4. The helper restores the head again, steps twice to cylinder 2, then steps
   before each track read. Its 75 iterations therefore read cylinders 3–77,
   side 0. Each reads `$F5`–`$FA` with the same 1024/512-byte schedule. This gives
   450 extents and 422,400 DMA bytes. All selected sectors have status zero and
   no fuzzy masks. The image's eight fuzzy sectors are on side 1 and are not
   part of this load.
5. The helper LONG at `$77C00` is `$0001997B`, or 104,827 LONGs. Starting at
   `$1000`, it XORs each LONG with `$AAAAAAAA`, subtracts the decreasing LONG
   count, rotates right by one, and stores the result. This decodes 419,308
   bytes, ending at `$675EC` exclusive. The last 3,092 DMA bytes are outside
   that decode and are retained in the separate full-buffer capture.
6. The original helper writes WORD 1 to `$1002` and jumps to `$1000`. The decoded
   WORD was `$8000`; both versions are preserved. The entry begins with a branch
   to `$106E`. Its startup reads `$1003`/`$1002`, consistent with a platform
   selector. Shared Amiga/ST semantics are a lead for later comparison, not a
   transferred annotation or a claim that the payloads are identical.

The FDC/side interpretation is checked against the pinned Hatari sources:
[`FDC_TypeI_StepIn` and STEP update handling](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/src/fdc.c),
[PSG disk selection](https://github.com/hatari/hatari/blob/b18511507bcf48dcf11f32b555774ea2f5e93fd0/src/psg.c)
and the source-bound loader instructions. This is static reconstruction of the
successful read path. It is not an observed WD1772/DMA/timing run.

## Captures and proof scope

| File | Bytes | Meaning |
| --- | ---: | --- |
| `boot_loader_known_prefix.bin` | 424 | Only source-backed boot copy/XOR output |
| `initial_loader_dma_decoded.bin` | 5,632 | Initial DMA buffer after its LONG XOR pass |
| `main_loader_helper.bin` | 512 | Copied helper after all four BYTE decode passes |
| `main_decoded.bin` | 419,308 | Main decoded range before the original selector store |
| `main_at_st_handoff.bin` | 419,308 | Same range after that store, ready at `$1000` |
| `main_dma_buffer_at_handoff.bin` | 422,400 | Full buffer, including unchanged trailing bytes |

The recipe binds all six exact hashes; generated reports carry the full source
mapping. The main handoff range SHA-256 is
`20c19400180d7e846b78aa615b68446293f8ca54015c4f4a42a77f03b24e8260`.
The pre-store decoded range SHA-256 is
`aca0db39a5657c952c5365e0201ac589cfdb53ea005c88d20a096d5891fae4ff`.

The generic mapped-execution adapter uses the existing generated C 68000
executor. It refuses unknown memory reads/fetches and undeclared writes. Hardware
access is not permitted. The slices stop before palette setup and resume at
self-contained decoder setup instructions after it. The disk reads themselves
are assembled from the proven static schedule; neither FDC results nor guest
state are forced to obtain a full-boot match. Different starting D/A register
seeds produce identical captures. This supports these initialized decoder
slices, not arbitrary register independence of the whole game.

The main decode takes 733,792 instructions; the original selector store and
jump take two more. Native execution matches an independently calculated private
recovery of the same bytes. The boot sector and fully decoded helper each
reassemble exactly through the native Atari raw-source API and independent
vasm (`-m68000 -no-opt -Fbin`). The instruction-only `assemble-file` CLI is not
the platform-source assembler. No full main-source restoration or exact build
of a restored main-source package is claimed yet.

## Tests and next work

`tests/test_stx_recovery.py` covers source identity, physical identity ambiguity,
ordered assembly and output bounds, fuzzy/missing reads, unknown reads/fetches,
undeclared writes, budget exhaustion, failed-state reuse and capture contracts.
Its optional `SGII_STX_IMAGE` case runs the actual recipe twice with different
register seeds. Existing STX differential/sanitizer and flat Atari/Amiga disk
checks remain applicable. The complete affected run has 68 tests: 67 pass; one
existing Ice-ADF test is skipped because its private fixture is absent. The
Windows export declarations are present; execution was tested on Linux.

Next import the source-bound artifacts as ST release targets through the shared
artifact/release model in proposal 047. Use load `$1000`, with pre-store and
handoff states kept distinct. Then analyze the ST startup and loader/runtime
reads before claiming that all required media or runtime initialization is
recovered. Do not resume unrelated Amiga naming or reconstruction work. A normal
media boot needs an ST-capable machine/FDC path; Copperline is an Amiga emulator
and is not evidence of that boot.
