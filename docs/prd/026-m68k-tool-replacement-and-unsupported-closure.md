# M68K Tool Replacement And Unsupported Closure

Status: Ready for issue execution
Source proposal: `docs/proposals/005-m68k-generated-coverage.md`
Created: 2026-05-16
Supersedes: None

## Problem Statement

After canonical form identity and generated sample plans exist, old runtime and generator paths can still preserve the wrong model: fallback scans, handwritten mnemonic-family switches, split disassembler identity, simulator lookup by mnemonic and operand shape, and unsupported lists outside generated coverage.

## Solution

Replace tool generators and runtime consumers with **Generated Tool Views** from the **Canonical Form Model**. Simulator/effect metadata, IR codec family behavior, assembler resolution, disassembler decode/render, and unsupported inventory must all consume generated metadata or report explicit generated-metadata gaps.

Final strict coverage is the rewrite gate only after legacy fallback paths are deleted.

Final coverage verification uses the canonical command surface:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase canonical
uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical
```

## User Stories

1. As a tooling maintainer, I want simulator/effect lookup by canonical form id, so that simulation does not rediscover instruction identity.
2. As a tooling maintainer, I want missing executor semantics reported as generated metadata status, so that downstream code does not guess behavior.
3. As a tooling maintainer, I want mnemonic families, condition-code families, size suffix rules, aliases, and render facts generated, so that C switches do not encode M68K knowledge.
4. As a tooling maintainer, I want assembler resolver tables generated, so that runtime assembly does not scan all forms.
5. As a tooling maintainer, I want disassembler ambiguity handled by generated metadata, so that runtime tie-breaking is not the safety net.
6. As a tooling maintainer, I want unsupported families classified in data, so that deferred work is explicit and stale-proof.
7. As a tooling maintainer, I want old split-identity and fallback paths deleted, so that there is one source of truth.
8. As a tooling maintainer, I want end-to-end strict coverage and oracle checks, so that the rewrite is proven across assembler, decoder, renderer, and simulator metadata.

## Implementation Decisions

- Migrate simulator/effect lookup to canonical form id.
- Generate semantic status and return `generated_semantics_missing` for forms without represented semantics.
- Replace handwritten IR codec family helpers with generated mnemonic or form metadata.
- Replace assembler and disassembler generator-local form logic with canonical model views.
- Keep unsupported families as structured **Unsupported Inventory** entries until the parser/schema/oracle story supports them.
- Treat decode sample gaps and asm/decode parity gaps as rewrite closure failures, not deferred family cleanup.

## Testing Decisions

- Test simulator/effect lookup by canonical form id.
- Test generated family metadata by removing old switch-list behavior from the tested path.
- Test assembler -> decoder -> renderer -> assembler parity where round-trip rendering is expected.
- Test unsupported inventory for MOVE16, FSAVE/FRESTORE, remaining PMMU, and generic coprocessor families.
- Run full strict coverage as the final gate.

## Out of Scope

- Implementing MOVE16, FSAVE/FRESTORE, PMMU, or generic coprocessor families unless their schema, sample plans, decode/render metadata, and oracle support are ready.
- Modifying vasm, Musashi, or other external oracles.
- Maintaining compatibility shims for replaced internal generated-table APIs.

## Acceptance Criteria

- Simulator/effect metadata lookup is keyed by canonical form id.
- Missing semantics are represented by generated status, not guessed downstream behavior.
- IR codec family and size-suffix behavior comes from generated metadata.
- Runtime assembler/disassembler fallback paths listed in the proposal are deleted or folded into generated metadata.
- Unsupported inventory is explicit, stale-proof, and checked by strict coverage.
- Final strict coverage and relevant oracle checks pass after fallback deletion.

## Deletion / Cleanup Expectations

- Delete runtime whole-form scans by mnemonic and operand shape.
- Delete simulator fallback lookup by mnemonic and expected operand kind.
- Delete handwritten downstream mnemonic-family switch lists.
- Delete runtime disassembler specificity scoring once generated sorting and ambiguity checks replace it.
- Delete diagnostic manifest code once canonical reporting fully replaces it.

## Verification

- Run strict form coverage tests.
- Run `uv run python -m amiga_reversing.tools.m68k_coverage check --phase canonical`.
- Run stale unsupported inventory tests.
- Regenerate assembler corpus.
- Run vasm oracle corpus checks where supported.
- Run C backend assembler/disassembler/simulator tests.
- Run executor tests only for forms with generated semantics.

## Open Questions

- None. Deferred families remain unsupported inventory until parser/schema/oracle support exists.
