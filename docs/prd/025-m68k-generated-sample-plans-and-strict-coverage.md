# M68K Generated Sample Plans And Strict Coverage

Status: Ready for issue execution
Source proposal: `docs/proposals/005-m68k-generated-coverage.md`
Created: 2026-05-16
Supersedes: None

## Problem Statement

Corpus generation owns too much M68K knowledge. Special operands, effective-address families, unsupported states, and sampleability are decided in generator code instead of generated metadata. This makes coverage hard to audit and easy to weaken.

## Solution

Move sample strategy into generated **Sample Plans** attached to **Canonical Forms**. Corpus generation becomes an interpreter of sample plans. Canonical strict coverage checks report and fail on unclassified forms, missing sample plans, stale unsupported reasons, asm/disasm identity mismatches, and missing generated semantics where required.

The final rewrite gate runs in PRD 026 after legacy fallback paths are deleted, so strict coverage cannot pass only because old runtime behavior masked bad metadata.

Canonical reporting and checks must use the shared coverage command surface:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase canonical
uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical
```

## User Stories

1. As a tooling maintainer, I want operand samples generated from KB or parser assertions, so that corpus code does not encode ISA knowledge.
2. As a tooling maintainer, I want effective-address coverage by family, so that one token sample is not mistaken for representative coverage.
3. As a tooling maintainer, I want sampleable and unsupported forms classified in generated data, so that coverage status is auditable.
4. As a tooling maintainer, I want stale unsupported reasons to fail, so that old TODOs cannot outlive their facts.
5. As a tooling maintainer, I want corpus generation to expand sample plans only, so that ownership is clear.
6. As a tooling maintainer, I want reports by CPU, mnemonic, EA family, alias, oracle, and unsupported state, so that gaps are visible.
7. As a tooling maintainer, I want strict coverage to gate required forms, so that generated tooling cannot silently regress.

## Implementation Decisions

- Generate operand-kind sample data from the KB or parser-asserted KB entries.
- Generate EA samples by required family and CPU tier.
- Represent sample status with explicit values such as sampleable, intentionally unsupported, implemented unsupported, and missing sample strategy.
- Keep unsupported reasons in structured data with stale-proof conditions.
- Make the corpus generator expand generated sample plans and record coverage results.
- Use strict coverage for required form classification, asm/disasm parity, alias targets, and stale unsupported inventory.
- Ensure canonical unsupported inventory exists before enabling canonical strict checks.
- Expose report and check behavior through `amiga_reversing.tools.m68k_coverage`; corpus-generation scripts may produce coverage inputs but must not become the user-facing coverage command surface.

## Testing Decisions

- Test sample-plan generation for special operand families and EA families.
- Test corpus output through observable generated cases, not private helper branches.
- Test stale unsupported inventory failures.
- Test strict coverage failures for missing sample strategy, unclassified forms, alias without target, and asm/disasm identity mismatch.
- Keep oracle checks black-box: vasm verifies assembler acceptance; generated tools consume their own metadata.

## Out of Scope

- Migrating every runtime tool consumer; PRD 026 owns final replacement and deletion.
- Implementing deferred unsupported instruction families.
- Adding executor semantics without generated semantic metadata.

## Acceptance Criteria

- Corpus generation no longer owns special M68K operand knowledge.
- Every required **Canonical Form** has a sample plan or explicit unsupported status.
- EA coverage reports required, covered, and missing families.
- Strict coverage fails on unclassified required forms and stale unsupported reasons.
- Report mode remains available for inspection without enabling strict failure.
- Canonical report and strict checks are available through `uv run python -m amiga_reversing.tools.m68k_coverage ... --phase canonical`.

## Deletion / Cleanup Expectations

- Delete corpus-local special operand guessing once generated sample plans cover the same behavior.
- Delete local unsupported lists detached from generated status.

## Verification

- Regenerate assembler corpus.
- Run corpus generation tests and canonical strict coverage checks.
- Run vasm oracle corpus checks for CPU tiers where oracle support exists.
- Run decode/disassembly parity report against generated sample cases.

## Open Questions

- None for ownership. Specific unsupported-family reasons can be refined as implementation exposes exact missing schema fields, but canonical unsupported inventory must exist before strict checks are enabled.
