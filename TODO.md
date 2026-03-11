# TODO

## vasm Bootstrap

- [x] Get vasm source, build locally (ext/vasm/)
- [ ] Document supported directives, pseudo-ops, and hunk output capabilities
- [x] Write minimal test programs to verify round-trip: source → assemble → binary
- [x] Use vasm as the assembler backend for test oracle
- [x] Identify limits/bugs as we push on edge cases (FPU, coprocessor, addressing modes)
- [ ] Document any patches we apply
- [ ] Derive assembler rule metadata from vasm by running vasm in discovery mode and emit a canonical `knowledge/vasm.json` assembler capability schema, then add a generated `knowledge/vasm_roundtrip_rules.json` that maps KB syntax to roundtrip-safe forms (size/pattern filters, skip-form lists, and canonical replacements) so roundtrip tests consume assembler intent from data only

## Disassembler & Verification

- [x] Build M68K disassembler — test-driven, using knowledge base (instructions, hardware registers, OS calls)
- [x] Build test oracle — assemble known source → binary → disassemble → reassemble → binary diff; drives error detection in data, tools, and references simultaneously
- [x] Derive M68K condition-family canonicalisation from KB data (including PMMU condition tables extracted from PDF)
- [ ] Round-trip validation tooling per CLAUDE.md: reassemble with vasm, binary-diff against original

## Data-Driven Audit — Disassembler (`m68k_disasm.py`)

Everything must be driven from `knowledge/m68k_instructions.json` parsed from the PDF.
KB loaders already exist (`_load_kb_encoding_masks`, `_load_kb_ext_field_map`, etc.) —
the infrastructure is proven, it just needs extending to cover all instructions.

## Data-Driven Audit — Round-Trip Tests (`test_m68k_roundtrip.py`)

### Medium

- [x] Bit-number immediate `#4` arbitrary (line 341) — acceptable test value, not derivable from KB
- [x] Bit-field `{2:8}` offset/width arbitrary (lines 486-498) — acceptable test values
- [x] Branch size `"b"`→`".s"` mapping — now from `vasm_compat.json` `branch_size_map`
- [x] LINK immediates hardcoded, no `immediate_range` in KB (lines 411-413)
- [x] `"movem"` string literal instead of `m_lower` parameter (lines 597-611)

## Compiler Fingerprinting

- [ ] Inventory available Amiga compilers (ADCD disc, archives) — SAS/C, Lattice, DICE, Aztec/Manx, GCC, etc.
- [ ] Run compilers under vamos to compile test programs at various optimization levels
- [ ] Extract signatures: startup code, function prologues/epilogues, runtime library functions, register conventions
- [ ] Build fingerprint database for auto-identifying compiler/language in unknown binaries

## Knowledge Base

- [ ] Refine OS version tagging — differentiate 570 "1.3" functions into 1.0/1.1/1.2/1.3 if possible
- [ ] Complete hardware register bit definitions (104/245 done)

## Disassembly

- [ ] Select a game binary to begin actual disassembly
