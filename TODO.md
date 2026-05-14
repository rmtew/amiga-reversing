# TODO

## Unsorted

Some of these may be in non-updated source in targets/, they need checking for existing fixes.

- Pandora observed improvement possibilities (target: `amiga_disk_pandora-1988-firebird__amiga_raw_pandora_3e1ee0f1_bk_00_000000e8`):
  - Amiga platform custom register propagation failure:
    ```
    04cc 3b7c86400096   move.w #DMAF_SETCLR|DMAF_BLITHOG|DMAF_MASTER|DMAF_BLITTER,dmacon(a5)
    04d2 610002f8       bsr.w abs_0_000107CC
    ...
    07cc              abs_0_000107CC:
    07cc 207c00077d00   movea.l #$77D00,a0
    07d2 2b480050       move.l a0,$0050(a5)
    ```
    - Despite the typed amiga platform `_custom` value of `a5` being used in the caller, it is not in the `callee`.
    - The value set in `a0` should be registered as a runtime memory range and given an equate, and added to memory map.
- Bloodwych observed improvement possibilities (target: `amiga_hunk_bloodwych`):
  - Web UI improvement possibilities for lookup tables samples:
    ```
      020e abs_0_000005B2:
      020e 00008e84                           dc.l abs_0_00008E84
      0212 00008f14                           dc.l abs_0_00008F14
      0216 00008ecc                           dc.l abs_0_00008ECC
      021a 00008f5c                           dc.l abs_0_00008F5C
      021e 00008ec8                           dc.l abs_0_00008EC8
      0222 0000                               dc.b $00,$00
    ```
      - Labels are not treated like `m68k_vector_spurious_interrupt` above (no link, no navigate lookup integration).
      - Trailing word should likely be `.w`.
    ```
      5548                  abs_0_000058EC:
      5548 0000               dc.w abs_0_000058F4-abs_0_000058F4
      554a 0018               dc.w abs_0_0000590C-abs_0_000058F4
    ```
      - Verify/finish link/navigate integration for word-relative lookup table labels.
  - Web UI improvement possibilities for ORG sections (or sections known to be bootstraped to addresses)
    ```
    | 5d5e | | abs_0_00006102: |
    ```
    - For these targets there would be value in a new column between hunk offset and hex value where we showed the
      execution/bootstrap address. While it is implied by the label, it is insufficient for user browsing.
    - Similarly a jump to address function in the web UI would be useful. Maybe alter the Navigate button or popup
      in some way to also offer that functionality for suitable targets.
- Bootblock regressions (amiga platform specific):
  - Why bootblocks are treated as a $70000 absolute target is unclear. They should be assumed to be position
    independent unless they bootstrap to absolute addresses internally:
    ```
        SECTION code,code
    loc_0_00000000:
        ORG $70000
    abs_0_00070000:
      dc.b "DOS",$00	; NOTE: boot magic
    ```
  - Substandard target: `targets\amiga_disk_epic-1992-ocean-disk-1\targets\amiga_raw_bootblock\bootblock.s`
    - We fail to symbolise the offsets for the struct we pass into `DoIO` in `a1`. 
    ```
    lea.l abs_0_0007020E(pc),a5
    movea.l (a5),a1
    move.l #$400,$002C(a1)
    move.l #$4E00,$0024(a1)
    move.l #$1E200,$0028(a1)
    move.w #$2,$001C(a1)
    movea.l $0004.w,a6
    jsr _LVODoIO(a6)
    ```
    - We fail to recognise that we read into `$1E200` and bootstrap to `$864` base range (missed entrypoint/code in
      `targets\amiga_disk_epic-1992-ocean-disk-1\targets\amiga_raw_bootloader_stage_1\bootloader_stage_1.s`?).
    ```
    abs_0_0007008C:
      move.w #$2FFF,d0
      lea.l $00020000.l,a0
      lea.l $00000864.l,a1
    abs_0_0007009C:
      move.b (a0)+,(a1)+
      dbf.w d0,abs_0_0007009C
      bsr.w abs_0_00070164
      jsr $0000086C.l
    ```
- Emulation-based tracing:
  - Local `WinUAE` usage (currently cloned to `resources/clone_common/WinUAE`):
    - It is unclear why some things are the way they are in the disassembled source code. Orphaned code blocks are one
      example of this. We should be able to use `WinUAE` (providing configuration on disk and on command-line and so on)
      and drive sessions from the command-line to take advantage of a) ability to run a target in a realistic setting
      b) to use the debugger to analyse memory and other state c) direct execution using breakpoint and more.
- Assembler correctness:
  - We used to have the ability to specify what assembler to render for. This might have been removed. However if we
    do any of the assembler correctness tasks that follow this entry we might want to bring it back.
  - We used to use `vasm` for binaries but `Genam` for instance failed the binary exactness requirement because one of
    the instructions (perhaps previously disassembled from `70ff4e75` preceding `h0_063E`?) used a byte constant but
    encoded the full word. In theory correct in the reproduction sense, but not correct in the precise sense of what is
    used. It would be good to use `vasm` for the roundtrip assembly again and try to do exact builds with that again to
    guard against our disassembler/IR/assembler looping on our system-wide misinterpretations.
  - We also have `Genam` accessible via `uv tool vamos` in theory. We should also be able to do a pass through that.    
- Codebase auditing/global refactoring:
  - A loose approach has been taken to using static string values and string comparison as an implementation approach
    and while some of that has been cleaned up, it would be good to do a comprehensive pass over the codebase. We should
    be using bitflags or enums to replace that.
  - A loose approach to arrays of booleans (likely uint8_t per flag) has been used as an implementation approach
    and it should use bitarrays instead at compile-time. The best approach might be #define and similar, although C99
    might provide compile-time approaches. This should be formalised in a common .c/.h location and used from there.
- One interesting facet of arena usage is that we have custom methods that work on arena memory. There is a good
  argument here to expand that for all our allocations, where for instance instead of using an arena we provide an
  allocator that happens to be an arena. It might also be worth abstracting it further to a context object that
  happens to have the preferred allocator as it's default allocator.
  - We should strongly consider using platform-specific allocations bypassing the C runtime with a view to not linking
    against it at a later date.
  - ...

### Damocles observations

Target: `amiga_disk_damocles-mercenary-ii-1990-novagen-cr-h__amiga_hunk_damocles_53b24620`

- Disk "damocles" target is not a standard decompression stub.
  - Several indicators each alone differentiates from standard decompression with or without bootstrapping:
    - Use of multiple hunks.
    - Presence of multiple payloads.
    - Non-trivial use of custom registers.
  - We should perhaps flag stub decompressors with "stub" badge.
- Disk "damocles" target analysis flaw indicators:
  - Second hunk:
    - Unresolved PC-relative labels:
      ```
      000c 287a00c4 movea.l $C4(pc),a4
      ...
      001e d1fafff4 adda.l -$C(pc),a0
      ```
      - This is likely because the `$c4` is picking the address to use out of the `lea` instruction leading what
        looks like a RLE post-pass. And the `-$C` is perhaps picking out the offset. If we have PC-relative references
        we are failing like this, we should perhaps put a label on the given instruction and do an intra-instruction
        addend to the numeric value within it. This way there's no inter-instruction addend and no chance of drift.
    - Non equated runtime address for tetragon decompression start address:
      ```
      002a 43f90004f92b lea.l $0004F92B.l,a1    
      ```
  - Third hunk:
    - Non-equated runtime addresses for post-pass RLE start and end addresses:
      ```
      00d0 41f900040000 lea.l $00040000.l,a0
      00d6 45f900050000 lea.l $00050000.l,a2
      ```
    - Entrypoint not load address for $100 bootstrapped payload.
      ```
      005c 4eea0040 jmp $0040(a2)
      ```
    - Invalid double ORG with invalid non-absolute labelling:
      ```
      0058 41fa00f2   lea.l loc_2_0000014C(pc),a0
      005c 4eea0040   jmp $0040(a2)
      ...
      006a            loc_2_0000006A:
                ORG $100
      006a            abs_2_00000100:
      ...
                ORG $14C
      014c            loc_2_0000014C:
      ```
      - `ORG $14C` seems like a false positive perhaps created by the PC-relative label?
      - `loc_2_0000014C` should be a local label created pre-jmp outside the abs range of the `ORG $100`?
      - It does compile exact so maybe it reflects correctness issues with our assembler and might fail with `vasm`?
        

## Phase 6: Beyond Static Analysis

Static analysis has reached its limits for GenAm at 28.5% core coverage.
The remaining code is reachable only through runtime-dependent dispatch
(callback pointers, input-dependent computed addresses).

### Emulation-Guided Coverage
- [ ] Instrumented vamos execution of GenAm with real source files
- [ ] Coverage feedback loop: emulation traces -> new entry points -> re-analyze
- [ ] Identify dead code: addresses never executed across all input variations

### Data Structure Enumeration
- [ ] Extend jump table pattern recognition for new table formats

## Round-Trip Validation

- [ ] Re-run round-trip validation for fresh GenAm / Bloodwych output after the shared-analysis and renderer refactors, then classify any remaining binary diffs as formatting churn vs real semantic regressions

## Knowledge Base: Amiga Platform

- [ ] Refine OS version tagging (570 "1.3" functions -> 1.0/1.1/1.2/1.3)
- [ ] Complete hardware register bit definitions (104/245 done)
- [ ] Extend NDK-derived hardware symbol coverage beyond `hardware/custom.i` and `hardware/cia.i` if targets use additional include-backed hardware families, so rendering stays source-accurate without falling back to generic absolute symbols
- [ ] Review entries in `knowledge/amiga_ndk_corrections.json` and promote `review_status` from `seeded` to `validated` only when a human has explicitly checked the cited source
- [ ] Add a seed-generation/review flow for corrections so autodoc-derived candidates can be proposed without being silently treated as validated KB
- [ ] Verify HUNK_OVERLAY format against ADCD primary source
- [ ] Add primary-source sample/fixture coverage for `HUNK_OVERLAY`; `vasm` hunk output has no overlay support, so this needs a different oracle or a vetted real sample

## Future Work

### M68K KB / Executor
- [ ] Add full upstream `RTE` stack/PC/SR semantics extraction to generated M68K metadata if a target needs it; keep this spec-driven, not executor-hardcoded
- [ ] Extend the new PDF-driven compare-swap KB semantics through full `CAS2` decode/disasm/executor support; current decoded operand model cleanly supports single-`CAS`, but `CAS2` still needs first-class paired-memory operand modeling

### M68K Assembler Coverage Audit
- [ ] Make the C assembler audit comprehensive over canonical generated forms, not just one representative sample per form
- [ ] Add explicit alias coverage on top of canonical-form coverage so generated syntax aliases are tested separately from canonical forms
- [ ] Generate multiple valid EA samples per canonical `ea` form from KB `EA_MODE_TABLES`, not just the first working mode
- [ ] Extend audit sample generation from the current basic operand classes to full special-form operand synthesis where generated form metadata is not enough on its own
- [ ] Move any remaining audit-side operand guessing into generated C metadata where possible, so the audit stops encoding assembler knowledge locally
- [ ] Add a strict failure for any new canonical generated form that has neither a sample strategy nor an explicit unsupported reason
- [ ] Add a strict failure for any stale explicit unsupported reason once the form becomes sampleable
- [ ] Consider adding a parallel decode/disasm generated-form coverage-contract slice so KB/form drift is checked on both assembler and decoder sides

### Remaining Assembler Coverage Work
- [ ] Implement `MOVEC` control-register syntax and remove its explicit unsupported forms from C assembler coverage tests
- [ ] Implement `MOVES` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `CHK2/CMP2` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement bitfield forms (`BFCHG/BFCLR/BFEXTS/BFEXTU/BFFFO/BFINS/BFSET/BFTST`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `CAS/CAS2` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement long multiply/divide register-pair syntax (`MULS/MULU/DIVS/DIVU` long forms) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `RTD` immediate extension encoding and remove its explicit unsupported form from C assembler coverage tests
- [ ] Implement `STOP` immediate extension encoding and remove its explicit unsupported form from C assembler coverage tests
- [ ] Implement `TRAPcc` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement `MOVE16` forms and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement FPU save/restore forms (`FSAVE/FRESTORE`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement PMMU forms (`PFLUSH/PFLUSHA/PFLUSHR/PMOVE/PRESTORE/PSAVE/PScc/PTRAPcc/PVALID/PBcc/PDBcc`) and remove their explicit unsupported forms from C assembler coverage tests
- [ ] Implement generic coprocessor forms (`cpBcc/cpDBcc/cpGEN/cpRESTORE/cpSAVE/cpScc/cpTRAPcc`) and remove their explicit unsupported forms from C assembler coverage tests

### M68K Generated Metadata / Audit Plumbing
- [ ] Export any additional generated C tables needed for audit/sample generation from the C metadata pipeline
- [ ] Decide whether special-form operand sample templates should live in generated C metadata instead of coverage helpers
- [ ] Clean up extension-word/form modeling where raw encoding counts exceed canonical form counts (`CHK2/CMP2`, bitfield ops, `CALLM`, PMMU families) so coverage tooling can reason about form support without encoding-level guesswork
- [ ] Replace mnemonic-specific audit overrides with generated canonical syntax metadata where possible
- [ ] Add a small report mode for the C coverage suite so unsupported-form inventory can be viewed without reading test code

### Compiler Fingerprinting
- [ ] Inventory Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC)
- [ ] Run under vamos, extract signatures (startup, prologues, runtime)
- [ ] Build fingerprint database for auto-identifying compiler/language

### Analysis Architecture
- [ ] Decide whether any remaining indirect-analysis orchestration in C should stay monolithic or split further from lower-level reusable analysis
- [ ] Add a small number of whole-target integration checks around GenAm / Bloodwych output so renderer and analysis regressions are caught above the unit-test level
- [ ] Keep strict `mypy` coverage focused on the Python web/orchestration layer and C-backed adapters
- [ ] Add first-class support for non-AmigaDOS/custom-track disks in the import path; current strict importer only accepts AmigaDOS disks
- [ ] Extract structured file-signature KB from primary or project-trusted sources so packer/cruncher detection is KB-driven instead of omitted
- [ ] Replace sector-image non-DOS heuristics with real raw-track/custom-loader format decoding once we ingest non-ADF track data or add custom-format descriptors to the KB
- [ ] Extend typed executable structure analysis beyond resident/library classification to parse Exec library init/vector structure and surface NDK-driven exported function names in the executable view
- [ ] Tighten the remaining resident/library/device structured-entrypoint work now that bootblocks and resident auto-init vectors are modeled: finish Exec init/vector executable-layout parsing from primary-source metadata for any still-missing formal entry code, make emitted/exported entry labels version-aware from the OS KB, and add whole-target regressions that pin real exported handler coverage/naming on resident binaries
- [ ] If we import seeded target-local facts from external reverse-engineering sources, keep them in an optional import workflow and never make tests, normal target rendering, or precommit depend on the external source being present
- [ ] Add Add Project UI flow for manual raw-binary targets that requires user-supplied load address and entrypoint, using the new strict `source_binary.json` raw-binary source kind
- [ ] Auto-create non-DOS loader stage targets only when bootloader analysis can materialize concrete stage bytes plus load address and entrypoint, so inferred-only regions stay honest
- [ ] Extend runtime-built Amiga resident/device analysis for targets such as `amiga_disk_carrier-command-1994-kixx-budget__amiga_hunk_devs__ramdrive.device_2c146d8c`, where resident/device structures and dispatch code are copied and relocated before `AddDevice`; keep any source refresh gated on clean direct rebuild or explicitly classified relocation semantics.
- [ ] Keep the mojibake check in `amiga_reversing.tools.check_mojibake` tight and data-oriented; if more broken encodings appear, extend the explicit pattern list with focused regression tests rather than broad punctuation bans
- [ ] Continue the remaining M68K/disasm audit slices beyond the assembler coverage work:
  - decoder/disassembler generated-form consistency in the C disassembler/IR metadata
  - unsupported special-form implementation vs generated-form cleanup in the C generator pipeline
  - any remaining honest unresolved indirect-call classification work in the analysis path if benchmarks expose avoidable `unknown` cases
