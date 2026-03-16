# TODO

## Phase 1: Complete the Knowledge Base

Extract all instruction metadata from the PDF into `m68k_instructions.json`.

### Encodings & Forms (done)
- [x] Opword bit patterns for all 127 instructions
- [x] Extension word fields (displacement, immediate data)
- [x] EA mode tables (src/dst/ea, 020+ markers)
- [x] Syntax forms and operand type patterns
- [x] Constraints (immediate ranges, CC parameterization, direction variants, etc.)

### Condition Code Semantics (done)
- [x] Parse CC description text from each instruction's "Condition Codes" section
- [x] Classify each flag effect into semantic rules (result-based, operand-based, operation-specific)
- [x] Emit structured `cc_semantics` per instruction in JSON (127/127 classified, hard-fail on unrecognized)

### SP Effects (done)
- [x] Parse Operation field into structured SP delta expressions
- [x] Classify: decrement N, increment N, displacement-adjust, load/save reg, compound (LINK/UNLK)
- [x] Emit per-instruction `sp_effects` in JSON (9 instructions, hard-fail on unmatched SP clauses)

### PC Effects (done)
- [x] Derive base instruction size from encoding structure (opword + extension words)
- [x] Flag control-flow instructions (branch, jump, call, return, trap) with conditional flag
- [x] Emit per-instruction `pc_effects` in JSON (22 control flow, no hardcoded mnemonic names)

## Phase 2: Data-Driven Assembler (done)

Reverse of the disassembler, driven from the same JSON.
`m68k/m68k_asm.py` -- 1299 tests, 90 mnemonics, 0 failures, 27 known divergences (imm routing).

- [x] Operand syntax → EA mode bits (parse register names, addressing modes, immediates)
- [x] Opword construction from encoding bit patterns + operand fields
- [x] Extension word generation (displacements, immediate data, bit fields)
- [x] Size suffix → size field encoding
- [x] Verify against vasm: 1273/1300 passed, 27 known divergences, 0 mismatches
- [x] Verify against DevPac GenAm 3.18: 1297/1301 passed, 4 known divergences, 0 mismatches
- [x] Unified oracle test harness: `scripts/test_m68k_oracle.py` (vasm | devpac)
- [x] Per-assembler behavior JSON: `knowledge/asm_vasm.json`, `knowledge/asm_devpac.json`
- [x] Branch/label support with PC-relative displacement calculation
- [x] SR/CCR/USP operand support (separate KB instructions)
- [x] Auto-routing aliases (ADD #imm → ADDI, DBRA → DBF, BLO → BCS)

## Phase 3: Data-Driven Effect Predictor (done)

Given an instruction + initial state, predict SP delta and CC result from KB rules.

- [x] SP predictor: consume JSON SP effects, compute stack pointer delta (including `load_from_reg` via `reg_state`)
- [x] CC predictor: consume JSON CC semantic rules, compute flag values from operands/result
- [x] PC predictor: next-PC calculation (sequential size from disassembler, branch targets)
- [x] Operation type classifier: Phase 11 in parser — classifies PDF `operation` text into structured types
- [x] Shift/rotate properties: `shift_count_modulus` and `rotate_extra_bits` extracted from PDF description/operation
- [x] Compute formulas: `compute_formula` extracted from PDF Operation text (63 instructions)
- [x] Specialized overflow rules: `overflow_add/sub/neg/negx/multiply` (parser-asserted, Track B)
- [x] Carry/borrow detection, shift carry/MSB semantics (parser-asserted, Track B)
- [x] Shift fill behavior: `fill` field on variants from PDF description (sign/zero/rotate)
- [x] Combined mnemonic variants: `processor_020` flag derived from form data
- [x] Implicit operands: `implicit_operand` extracted from PDF Operation text
- [x] Size-by-EA-category: `size_by_ea_category` extracted from PDF description (register=long, memory=byte)
- [x] CC result width override: `cc_result_bits` extracted from PDF CC descriptions (SWAP: 32-bit despite Size=Word)
- [x] Sign-extend formula: `sign_extend` with `source_bits_by_size` from PDF description text
- [x] CCR bit positions: `ccr_bit_positions` in KB `_meta` (parser-asserted, PDF p21 Figure 1-8)
- [x] Condition test definitions: `cc_test_definitions` in KB `_meta` (parser-asserted, PDF pp 90-91 Table 3-19)
- [x] Source sign-extension: `source_sign_extend` from PDF description + opmode_table (ADDA, SUBA, MOVEA, CMPA)
- [x] Transfer layout: `transfer_layout` from PDF description (MOVEP: stride=2, byte_order=big_endian)
- [x] Bounds-check trap condition: `trap_condition` from PDF operation text (CHK: signed, 0 ≤ Dn ≤ Source)

## Phase 4: Verification Harness (done)

machine68k (Musashi) as independent oracle for execution semantics.
`scripts/test_m68k_execution.py` -- 4870 tests, 119 mnemonics, 0 failures.
`m68k/m68k_compute.py` -- KB-driven compute engine (CC/SP/result prediction, condition evaluator).

- [x] Test generator: KB-driven discovery of testable instructions, deterministic test values
- [x] Runner: instruction hook captures post-execution state without sentinel interference
- [x] Comparator: predicted CC/SP/PC vs machine68k actual, per-flag reporting
- [x] Compute module extracted: `m68k_compute.py` — pure functions, no machine68k dependency

### CC verification (54 mnemonics)
- [x] ALU register-register: ADD, ADDX, SUB, SUBX, CMP, AND, OR, EOR, MOVE, NEG, NEGX, NOT, CLR, TST (14 mnemonics, 1512 tests)
- [x] Shift/rotate: ASL, ASR, LSL, LSR, ROL, ROR, ROXL, ROXR (8 mnemonics, 1296 tests)
- [x] Multiply: MULS, MULU (2 mnemonics, 72 tests) — KB `compute_formula` + `overflow_multiply` rule
- [x] Divide: DIVS, DIVU (2 mnemonics, 84 tests) — KB `compute_formula` + `division_overflow`/quotient CC rules
- [x] Bit test: BTST, BCHG, BCLR, BSET (4 mnemonics, 192 tests) — KB `compute_formula` (bit_test/change/clear/set) + `bit_zero` rule
- [x] EA mode `#imm,Dn`: ADDI, ADDQ, ANDI, CMPI, EORI, ORI, SUBI, SUBQ (8 mnemonics, 540 tests) — `imm_dn` form type
- [x] Direct Dn form: SWAP, EXT (3 mnemonics, 108 tests) — KB `sign_extend` + `exchange` formulas, `cc_result_bits`, `["dn"]` form type
- [x] Memory compare: CMPM (1 mnemonic, 108 tests) — `postinc_postinc` form type with memory test infrastructure
- [x] Address register compare: CMPA (1 mnemonic, 72 tests) — `dn_an` form type, KB `source_sign_extend` + `cc_result_bits`
- [x] TAS (1 mnemonic, 36 tests) — KB `msb_operand` CC rule, `test` compute formula, `single_op` form type
- [x] BCD: ABCD, SBCD, NBCD (3 mnemonics, 108 tests) — KB `add_decimal`/`subtract_decimal` compute formulas, `decimal_carry`/`decimal_borrow` CC rules
- [x] CCR/SR manipulation: ANDI/ORI/EORI/MOVE to CCR, ANDI/ORI/EORI to SR (7 mnemonics) — KB `ccr_op`/`sr_op` bypass, `imm_bit_*`/`source_bit` rules
- [x] MOVEQ (1 mnemonic) — KB `imm_dn` form type with signed byte immediate range

### SP verification (9 mnemonics)
- [x] PEA, JSR, BSR, RTS, LINK, UNLK (9 tests)
- [x] MOVEM (4 tests) — push/pop via `-(A7)`/`(A7)+`, SP delta = register_count × size
- [x] RTR (1 test) — return + restore CCR from stack, KB `loaded_from_stack` CC rule

### Register/flow verification (10 mnemonics)
- [x] An-destination: ADDA, SUBA, MOVEA (.W + .L) — KB `source_sign_extend` + `cc_result_bits` for .W sign-extension
- [x] EXG: 3 forms (Dx/Dy, Ax/Ay, Dx/Ay) — KB `operation_type=swap`
- [x] LEA: indirect, displaced, absolute — KB `compute_formula`
- [x] MOVE from SR — verify CCR bits in result
- [x] NOP, BRA, JMP — PC advancement / unconditional flow

### Condition test verification (46 mnemonics)
- [x] Scc: 16 conditions × 12 CCR states — KB `cc_test_definitions` + `evaluate_cc_test()`
- [x] Bcc: 14 conditions × 12 CCR states (taken/not-taken PC) — KB `cc_test_definitions`
- [x] DBcc: 16 conditions × scenarios (cc-true/loop/exhaust) — KB `cc_test_definitions`

### Peripheral/bounds verification (2 mnemonics)
- [x] MOVEP: memory→register byte-striped read — KB `transfer_layout` (stride, byte_order)
- [x] CHK: non-trapping bounds check — KB `trap_condition` (signed comparison, lower/upper bounds)

### Untestable (12 KB entries)
- 6 privileged: MOVE USP, MOVE to SR, RESET, RTE, STOP, PTRAPcc
- 4 exception-generating: TRAP, TRAPV, ILLEGAL, BKPT
- 2 partially tested: CHK (trapping path needs exception handler), MOVEP (reg→mem needs memory capture)

### Audits
- [x] Three audits passed — no hardcoded M68K knowledge, no silent fallbacks
- [x] All KB fields consumed: cc_semantics, operation_type, sp_effects, pc_effects, shift_count_modulus, rotate_extra_bits, compute_formula, bit_modulus, size_by_ea_category, cc_result_bits, ccr_bit_positions
- [x] Tier 5 audit: compute semantics moved from hardcoded handlers to KB `compute_formula`
- [x] Tier 5 audit: overflow rules specialized, fill/implicit defaults replaced with hard errors
- [x] Tier 5 audit: 020+ variant skip moved from string heuristic to KB `processor_020` flag
- [x] Tier 6 audit: CCR bit positions from KB, implicit_operand hard error, Track B citations on MODE_MAP/CPU_HIERARCHY/SIZE_MAP/coprocessor
- [x] Tier 6 audit: size_by_ea_category eliminates silent .b assembly-failure skip for bit tests
- [x] Tier 6 audit: EXTB source_bits derived from PDF bit number, cc_result_bits checks all 5 flags
- [x] Tier 7 audit: sign-extension from KB `source_sign_extend`, MOVEP from KB `transfer_layout`, CHK from KB `trap_condition`
- [x] Tier 7 audit: dead code removed (MOVEP reg→mem), assembly failure warnings added (Scc/Bcc/DBcc)

## Phase 5: Symbolic Executor (in progress)

KB-driven abstract interpretation engine for static analysis of disassembled code.
`m68k/m68k_executor.py` — block discovery, demand-driven disassembly, structured EA decoding.
Foundation: `m68k/m68k_compute.py` (verified against Musashi with 4870 tests).

- [x] `predict_pc()`: KB `pc_effects` + `opword_bytes` for branch target resolution
- [x] EA decoder: structured `Operand` from opcode bits via KB `ea_mode_encoding` + `ea_brief_ext_word`
- [x] EA resolver: translate Operand to effective address from abstract state
- [x] Abstract state model: `CPUState` — register file + CCR, layout from KB `movem_reg_masks` + `ccr_bit_positions`
- [x] Basic block discovery: two-pass flow-following with demand-driven disassembly (handles mixed code/data)
- [x] Cross-reference tracking: branch, jump, call, fallthrough xrefs with conditional flag
- [x] Branch target extraction: KB `displacement_encoding` (word/long signals), KB encoding fields for JMP/JSR EA
- [x] CC family resolution: KB `cc_parameterized` prefix lookup (Bcc, Scc, DBcc, PTRAPcc)
- [x] Audit: no hardcoded M68K knowledge — opword size, register counts, flag names, CC families, displacement signals all from KB
- [x] Memory model: `AbstractMemory` — sparse byte-granularity map, big-endian read/write at b/w/l sizes
- [x] State propagation: `propagate_states()` — BFS walk, per-instruction abstract execution, conservative join at merge points
- [x] Instruction effects: MOVE/MOVEA/MOVEQ, LEA, ADD/SUB/AND/OR/EOR, CLR, EXG, SWAP, EXT, NEG, NOT, TST, SP effects
- [x] Verification: 8 tests in `tests/test_executor_propagation.py` (memory r/w, copy, join, MOVEQ+LEA through memory, ADD, CLR, merge, EXG)
- [x] Audit: `_apply_instruction` dispatch via KB `compute_formula.op`/`operation_type` — no mnemonic-string dispatch
- [x] Audit: sign-extension from KB fields (`immediate_range.bits`, `source_sign_extend`, `source_bits_by_size`, `range_a/range_b`)
- [x] Audit: `sp_effects.bytes` hard error on missing, unused imports/variables removed
- [x] Entity integration: `scripts/build_entities.py` — hunk parse + executor -> entities.jsonl
  - Subroutine-level entities from call targets + block reachability
  - Bidirectional xrefs (calls/called_by) from executor XRefs
  - Reloc-derived data references for uncovered regions
  - Gap filling for 100% address coverage
  - `validate.py` PASS: 0 errors, 0 warnings, 0 unresolved xrefs
- [x] Jump table detection: 4 dispatch patterns (A-D)
  - EA mode detection from KB `ea_mode_encoding` (pcindex, index, ind, pcdisp)
  - BRA opcode pattern from KB encoding fields + `displacement_encoding`
  - Brief + full extension word formats from KB `ea_brief_ext_word`/`ea_full_ext_word`
- [x] Indirect target resolution: all register-indirect EA modes via KB-driven decode
  - `_decode_ea` + `resolve_ea` replaces hardcoded (An)-only check
  - Handles ind (An), disp d(An), index d(An,Xn) uniformly
  - RTS reads from pre-pop SP (KB `sp_effects.bytes` adjusts post-increment exit state)
  - Address size derived from KB RTS sp_effects -> size_byte_count (not hardcoded "l")
  - Alignment mask from KB `opword_bytes`, mode set from KB `ea_mode_encoding`
  - Table scan stride/bounds from KB `size_byte_count["w"]` (not hardcoded 2)
- [x] Per-caller context-sensitive analysis: `resolve_per_caller()`
  - Re-analyzes shared subroutines per call site when merged state loses caller info
  - Handles trampolines (pop return addr + jmp d(An)) and dispatch routines (jsr d(An,Xn))
  - Base register restored from platform config for callers where it was clobbered
  - 37 tests in `tests/test_indirect_resolution.py`: EA mechanics, trampoline, dispatch, struct field, PEA+RTS, table enumeration, register survival, backward slice, jump table patterns A-D, edge cases
- [x] Heuristic subroutine scan: RTS-bounded sequences scored against relocs/call targets
- [x] Scratch register invalidation after calls (KB `pc_effects.flow.type == "call"`)
- [x] OS library call identification: ExecBase load + LVO dispatch → function names
  - ExecBase addr from OS KB `exec_base_addr`, library names from `lvo_index`
  - MOVEA/JSR encoding fields from KB (not hardcoded bit positions)
  - Library base tagging: OpenLibrary return tagged via KB `returns_base` field
  - Tags propagate through registers, memory round-trips, state joins
- [x] Subroutine naming: OS call patterns, PC-relative string references, call graph
- [x] Shared KB utilities: `m68k/kb_util.py` (KB class, xf, find_containing_sub)
- [x] Predecrement/postincrement EA support: `-(An)` and `(An)+` in operand resolution + writes
- [x] Stack tracking: sentinel SP enables push/pop through abstract memory
  - JSR/BSR write return address to stack (enables RTS resolution)
  - Call fallthrough adjusts SP for callee's return (convention-based)
  - Displacement parsing consolidated via `_parse_disp()` helper
- [x] Memory allocation tracking: OS KB `returns_memory` field (AllocMem, AllocVec, etc.)
  - Parser-asserted from NDK autodocs in `parse_ndk.py`
  - Sentinel concrete addresses assigned to allocation results
  - Base register discovered from init pass (single-entry analysis)
- [x] App base register tracking: AllocMem → movea.l D0,An detected
  - Two-pass analysis: init pass discovers base reg + memory state
  - Init memory carried forward (library base tags in d(An) slots)
  - Convergence check includes tag comparison (not just concrete values)
  - 63% of blocks now have concrete A6 (enables d(A6) memory ops)
- [x] RTS return resolution: reads return address from stack via propagated SP + memory
- [x] Audit: hunk parser fully KB-driven — type IDs, masks, multipliers, ext packing, MemType all from JSON
- [x] Audit: _is_valid_68000 uses KB `processor_020` flag, not hardcoded mnemonics
- [x] Audit: _RELOC_INFO loaded from KB `relocation_semantics`, not hardcoded dict
- [x] Audit: build_reloc_map handles all absolute reloc types from KB
- GenAm results: 34.4% core (3109 blocks, 7393 instructions), 20.6% hints (1795 blocks)
- [x] Jump table structured emission: word-offset and self-relative tables as `dc.w target-base`
  - base_addr and table_end added to jump_tables.py return dicts
  - pc_inline_dispatch tables emitted as decoded BRA instructions
  - Jump table target labels get `; jt: base_label` comments
- [x] Jump table + indirect target discovery loop in gen_disasm.py
  - Iterates until stable, feeding jump table targets and resolved indirect targets as core entries
- [x] Code section memory reads: AbstractMemory falls back to code bytes for unmapped addresses
  - Resolves indirect calls through data pointers (longword pointer tables)
  - 3 pytest tests verify resolution and block discovery
- [x] Instruction validation (KB-driven):
  - EA mode validation against KB `ea_modes` (ea/src/dst keys)
  - An size restriction from KB `an_sizes` constraint (ADDQ/SUBQ byte to An)
  - An byte-size rejection from KB `ea_mode_sizes`
  - Branch target word-alignment from KB `opword_bytes`
  - 68020+ architecture comments from KB `processor_min` + variant `processor_020`
- [x] Hint block validation: block-level rejection (not per-instruction)
  - Flow-terminating last instruction required
  - Zero opword ($0000) rejects entire block
  - Invalid EA, odd branch target, 68020+ instruction rejects entire block
  - Hint blocks overlapping core code_addrs filtered out
- [x] Label cleanup:
  - Fallthrough-only labels removed (only branch targets get labels)
  - Hint successor labels: `hint_` for hint targets, `loc_` for core code targets
- [x] PC-relative target discovery from hint blocks (reduces vasm warnings)
- [x] Parser extended:
  - `an_sizes` constraint extracted from PDF description (ADDQ/SUBQ)
  - `ea_is_source` derived from opmode operation text arrow direction
  - `rx_mode`/`ry_mode` for EXG from description text
  - `operation_class` from instruction title (LEA, MOVEM)
  - 8 `_meta` fields added (size_suffixes, default_operand_size, register_aliases, ea_full_ext_bd_size)
- [x] pytest suite: `py -m pytest tests/` -- 1901 tests in ~2s
  - `test_m68k_roundtrip.py`: 1796 KB-driven roundtrip tests, batch-assembled (12 vasm calls)
  - `test_indirect_resolution.py`: 39 tests (dispatch patterns, backward slice, per-caller, inline data skip)
  - `test_executor_propagation.py`: 8 tests (memory, joins, instruction effects)
  - `test_executor_effects.py`: 49 tests (compute ops, preservation, merge, init mem join, multi-entry, return value summaries)
  - `test_analysis.py`: 6 tests (pipeline, save/load cache, version check)
  - `test_code_section_reads.py`: 3 tests (pointer resolution through code data)
- [x] PEA EA mode validation: guard against invalid modes via KB `ea_modes.ea`
- [x] Backward slice: skip call predecessors to prevent false-positive RTS resolutions
- [x] `_scan_inline_dispatch`: diagnostic stderr on decode errors
- [x] Jump table patterns A-D: dedicated regression tests
- [x] Package restructure: `m68k/` library, `scripts/` CLI tools, `tests/` pytest
- [x] Shared analysis pipeline: `m68k/analysis.py` with `analyze_hunk()` + `HunkAnalysis`
  - Both build_entities and gen_disasm use the same pipeline (eliminated ~441 lines duplication)
  - Cached results: `HunkAnalysis.save/load` via pickle (gen_disasm: 12s -> 0.7s with cache)
- [x] Executor refactored: `_apply_instruction` split into dispatch + handler functions
  - `decode_instruction_ops()`: shared operand decode (DecodedOps dataclass)
  - `_apply_binary_op()`: unified add/sub/and/or/xor handler (was 4 copies)
  - `_resolve_os_call()`: OS call resolution separated from instruction effects
  - `_apply_instruction`: 92-line table-driven dispatch (was ~850 lines)
  - `_apply_computed()`: KB-driven fallback via m68k_compute for all remaining ops
  - Bug fix: SWAP now works for encodings without MODE field
- [x] All 21 KB compute_formula ops handled (was 10, shift/rotate/multiply/divide/bit ops added)
  - Uses verified m68k_compute._compute_result (4870 Musashi tests)
  - Context from KB: shift_count_modulus, direction from dr field, fill from variants,
    bit_modulus from instruction, data_sizes from forms, i/r field for count source
- [x] Base register restoration after merge points (prevents A6 loss through joins)
- [x] Init memory join semantics: `_join_states` uses init_mem as default for missing bytes
  - Replaces unsound post-join restoration (which overrode explicit unknown writes)
  - Init bytes survive joins where no predecessor touched them
  - Explicit writes (even unknown) correctly kill init values at merge
  - Store pass broadened: removed code-range filter on captured values
  - 6 tests: survive join, cross-sub dispatch, local override, unknown-write kill, concrete disagree, both-agree
- [x] Audit: KB.addr_mask replaces hardcoded 0xFFFFFFFF, SWAP/EXG detected in
  _reg_modified_in_sub, invalidation path respects write_to_ea, i/r encoding
  field distinguishes immediate vs register shift counts
- [x] Performance: build_entities 28s -> 12s, gen_disasm 12s -> 0.7s (cached)
  - KB caching: module-level singletons, mnemonic/size/entry caches, EA reverse lookup
  - Targeted per-caller resolution: register substitution (O(1)) vs full propagation
  - Pipeline convergence skip: no redundant resolution after entry-point convergence
- [ ] Improve coverage beyond 34% (current focus):
  - [x] Add dispatch pattern D to `jump_tables.py`: LEA d(PC),An; MOVE.W d(An,Dn),Dn; JSR d(An,Dn)
    - Word-offset table at $0E9A, 29 entries (base-relative to A1=$0EA2)
    - Separate MOVE.W reads offset from table; JSR dispatches via same base register
    - JSR dispatch targets injected into call_targets for subroutine map (+38 subroutines)
  - [x] Init memory join semantics: values survive merges soundly (no false restoration)
    - Store pass captures all concrete app-base values (219 across 3 passes)
  - [x] Coverage gap diagnostic: 27 unresolved jumps, 307 unresolved returns
    - 16 jsr d(a6) already resolved by OS call identification (exec/dos library calls)
  ### Core expansion blockers (entry-point reachable, ordered by impact)
  - [x] Multi-entry propagation seeding: all entry points get exit states
    - Was: 2159/3109 blocks with exit states. Now: 3109/3110
    - Jump table targets: 28/29, 21/21, 26/27 (was 2/29, 2/21, 9/27)
    - propagate_states seeds all is_entry blocks, not just base_addr
  - [x] Inline data skip at $1754: per-caller already resolves this pattern
    - Tests confirm: BSR pushes return addr, callee pops, jmp 2(a0) resolves
    - GenAm's $1754 is embedded in larger sub, needs intra-sub flow tracing
  - [x] Summary-aware scratch invalidation: preserved/produced regs survive calls
    - 29/193 subs produce concrete return values (LEA target, constants)
    - Scratch invalidation skips summary-proven preserved AND produced regs
  - [x] Return value summaries: callee-produced concrete values propagate to callers
    - _compute_summary captures produced_d/produced_a (concrete at all RTS exits)
    - _apply_summary sets produced regs to concrete values, not unknown
  ### Resolved at higher level (not blocking core)
  - [x] 14 ExecBase LVO calls ($A910-$B06E): tagged A6 resolved by os_calls
    - movea.l ($0004).w,a6 correctly tags A6 with exec.library
    - _find_unresolved reports them but os_calls identifies all 39 library calls
  - [x] dos_dispatch at $B0F0: polymorphic by design, resolved per-caller
    - 22 dos.library calls resolved at each caller's BSR site via os_calls
    - $B0F0 is the shared dispatch block, will never resolve to single target
  ### Remaining genuine blockers (12 sites, 3 tractable)
  - [ ] Callback trampolines at $3AB0 and $4370: jsr (a0) with A0 from sub $3ED6
    - $3ED6 summary: A0 not preserved, not produced (input-dependent return)
    - Needs per-caller summary evaluation: re-run $3ED6 per caller's inputs
    - Only tractable remaining blocker with concrete analysis path
  - [ ] A2 dispatch cluster at $8A4A-$8F3A: 5 unresolved jsr/jmp (a2)
    - Callback function pointers (number formatting routine)
    - A2 likely set by callers as runtime-dependent function pointer
  - [ ] Runtime-dependent dispatches (not statically resolvable)
    - $B0DE: jsr (a0) double-indirect through sentinel memory chain
    - $8D44: jsr (a3), $901E: jsr (a4) -- unknown source
    - $1754: jmp 2(a0) embedded inline skip, needs intra-sub per-caller
  ### Deferred (not entry-0 reachable)
  - [ ] d(4300)(A6) LVO calls ($AA6A, $ABF6, $AC0A): hint-only, not entry-0 reachable
  ### Deferred (hint-only, not blocking core)
  - [ ] String dispatch table at pcref_3f3c: 65 assembler directives with self-relative handler offsets
    - Currently only in hint territory -- defer until core expansion reaches it
    - Requires per-instruction state tracking (register modified in loop)
  - [ ] Computed PEA+RTS dispatch at $7550: addresses $16E0-$1D14 (2.6KB addressing mode handlers)
    - Currently only in hint territory -- defer until core expansion reaches it
    - LEA $1D14(PC) + ADDA.W D3 + push + RTS -- D3 from instruction encoding table
  - [ ] Jump tables discovered only through hint blocks
    - Note their existence but don't analyze until reachable from entry point
- [x] Disassembly generator: `scripts/gen_disasm.py` -> `disasm/genam.s`
  - Core analysis with jump table + indirect target discovery loop
  - Hint blocks with block-level validation (flow, zero opword, EA, arch, alignment)
  - Label replacement: branch targets, relocated absolutes, PC-relative, immediates
  - Data regions as dc.b with dc.l at reloc offsets, strings as dc.b "text",0
  - Jump tables as dc.w target-base, inline dispatch as decoded BRA instructions
  - 020+ instructions emitted with `; 68020+` architecture comments
  - LVO symbols, argument constants, struct field substitution, app memory offsets
- [x] vasm assembly: zero errors, warnings only (absolute displacements in hint blocks)
- [ ] GenAm self-assembly round-trip: disassemble → reassemble with GenAm via vamos → binary diff

## Existing Infrastructure

### vasm Bootstrap
- [x] Get vasm source, build locally (ext/vasm/)
- [ ] Document supported directives, pseudo-ops, and hunk output capabilities
- [x] Write minimal test programs to verify round-trip: source → assemble → binary
- [x] Use vasm as the assembler backend for test oracle
- [x] Identify limits/bugs as we push on edge cases (FPU, coprocessor, addressing modes)
- [ ] Document any patches we apply
- [ ] Derive assembler rule metadata from vasm discovery mode → `vasm.json` schema

### Disassembler & Round-Trip
- [x] Build M68K disassembler — test-driven, using knowledge base
- [x] Build test oracle -- assemble -> disassemble -> reassemble -> binary diff (1796 tests, 110/126 mnemonics, batch-assembled)
- [x] Derive M68K condition-family canonicalisation from KB data (including PMMU condition tables)
- [x] Round-trip validation: GenAm → disasm → vasm → binary-diff = 0 bytes, 0 relocs different

### Data-Driven Audit — Round-Trip Tests
- [x] Bit-number immediate `#4` arbitrary — acceptable test value, not derivable from KB
- [x] Bit-field `{2:8}` offset/width arbitrary — acceptable test values
- [x] Branch size `"b"`→`".s"` mapping — now from `vasm_compat.json`
- [x] LINK immediates — now from KB `immediate_range` (extension word displacement extraction)
- [x] `"movem"` string literal — now uses `m_lower` parameter

## Future Work

### Compiler Fingerprinting
- [ ] Inventory available Amiga compilers (SAS/C, Lattice, DICE, Aztec/Manx, GCC, etc.)
- [ ] Run compilers under vamos to compile test programs at various optimization levels
- [ ] Extract signatures: startup code, prologues/epilogues, runtime library functions
- [ ] Build fingerprint database for auto-identifying compiler/language in unknown binaries

### Knowledge Base — Amiga Platform
- [ ] Refine OS version tagging — differentiate 570 "1.3" functions into 1.0/1.1/1.2/1.3
- [ ] Complete hardware register bit definitions (104/245 done)
- [x] Hunk format KB: `amiga_hunk_format.json` from NDK DOSHUNKS.H + LOADSEG.ASM
  - 26 hunk types, 19 ext types, memory flags, relocation semantics
  - Wire formats parser-asserted from LOADSEG.ASM with line citations
  - V37 compatibility note (HUNK_DREL32 = RELOC32SHORT in executables)
  - HUNK_DEBUG LINE sub-format (vasm/GenAm debug info)
- [ ] Verify HUNK_OVERLAY format against ADCD primary source (currently from .md)
- [ ] Investigate HUNK_LIB/HUNK_INDEX format (no NDK documentation found)

### Disassembly — GenAm
- [x] Target binary: GenAm (DevPac 3.18 assembler), 64920-byte CODE hunk
- [x] Code coverage: 59.3% (5280 blocks, 12640 instructions)
- [x] 374 subroutines, 13 named, 524 entities with 100% address coverage
- [x] OS call identification: 16 calls found, 13 resolved (exec.library)
- [ ] GenAm self-assembly round-trip: disassemble → reassemble with GenAm via vamos → binary diff
- [x] App base register tracking (A6 as data pointer for GenAm's work area)
- [ ] Name more subroutines (call graph analysis, data flow, hardware register access patterns)
