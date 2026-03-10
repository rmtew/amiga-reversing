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
- [ ] Round-trip validation tooling per CLAUDE.md: reassemble with vasm, binary-diff against original

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
