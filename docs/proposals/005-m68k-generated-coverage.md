# Proposal 005: M68K Generated Coverage

## TODO Coverage

- `TODO.md` M68K KB / Executor.
- `TODO.md` M68K Assembler Coverage Audit.
- `TODO.md` Remaining Assembler Coverage Work.
- `TODO.md` M68K Generated Metadata / Audit Plumbing.
- `TODO.md` Analysis Architecture: remaining M68K/disasm audit slices.

## Current State

- `knowledge/m68k_instructions.json` is generated from the PRM parser, with parser assertions in `src/scripts/kb/m68k_parser.py`.
- The C assembler and disassembler consume generated metadata under `src/generated/`.
- `src/scripts/generate_c99_assembler_subset.py` exports generated form metadata for supported assembler forms.
- `src/scripts/generate_c99_assembler_corpus.py` generates oracle/corpus cases but still carries local sample synthesis logic.
- The TODO unsupported list is concentrated around special-form operands and multi-word encodings: `MOVEC`, `MOVES`, `CHK2/CMP2`, bitfields, `CAS/CAS2`, long mul/div pairs, `RTD`, `STOP`, `TRAPcc`, `MOVE16`, FPU, PMMU, and generic coprocessor forms.

## Clean Near-Term Work

1. Make the generated form contract explicit.
   - Every canonical generated assembler form has one of: sampleable, implemented-unsupported, or intentionally-unsupported.
   - Unsupported reasons are generated or declared in one inventory, not scattered through tests.
   - Stale unsupported reasons fail once a form becomes sampleable.

2. Move operand knowledge out of audit helpers.
   - Add generated syntax/sample metadata for special operands where the KB already knows the fields.
   - Keep corpus generation mechanical: choose values from generated metadata and KB EA tables.
   - Avoid mnemonic-specific corpus guesses except as temporary entries in the unsupported inventory.

3. Expand EA sampling.
   - Generate multiple valid EA samples per canonical `ea` form from generated EA mode tables.
   - Cover register, memory, PC-relative, immediate, indexed, and restricted forms according to KB constraints.

4. Implement remaining special forms one family at a time.
   - For each family, update the parser/schema if needed, regenerate metadata, implement parse/encode/decode/executor support, then remove the unsupported inventory entries.
   - Start with narrow high-value forms (`RTD`, `STOP`, `MOVEC`) before larger families (`PMMU`, generic coprocessor).

5. Add decode/disasm coverage parity.
   - The same generated form inventory should drive assembler and decoder/disassembler coverage reports.
   - Coverage tooling should reason about canonical forms, not raw encoding-row counts.

## Better Version

- Generate a form coverage report that lists canonical forms by mnemonic, CPU, operand kinds, sample status, implementation status, and oracle coverage.
- Use one generated metadata model for parse, assemble, decode, disassemble, corpus sampling, and coverage reporting.
- Treat executor support separately from assembler/disassembler support, but tie both to the same KB semantics.

## Larger Architecture Notes

- No M68K instruction behavior should be hardcoded downstream. If `RTE`, `CAS2`, or PMMU needs richer modeling, extend the KB/schema and regenerate.
- Special-form handling is acceptable in generators when it is sourced from parser-asserted KB facts with citations.
- Coverage is a contract for generated metadata quality, not just a test corpus size metric.

## Verification

- Strict coverage tests for unsupported inventory completeness and staleness.
- Oracle corpus regeneration for each CPU tier.
- C backend assembler/disassembler tests for each newly supported family.
- Executor tests only after generated semantics exists.
- A report mode for current unsupported-form inventory.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16. Scope is coherent as proposal work; no implementation is claimed here.
