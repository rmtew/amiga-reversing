# M68K Canonical Form Model

Status: Ready for issue execution
Source proposal: `docs/proposals/005-m68k-generated-coverage.md`
Created: 2026-05-16
Supersedes: None

## Problem Statement

M68K tooling still has split form identity. Assembler metadata and disassembler metadata each describe forms, then runtime code joins them back together with indexes and fallback logic. This allows nullable ids, dense rows, aliases, and tool-specific form identities to be confused.

## Solution

Generate one **Canonical Form Model** from the **PRM-Derived Knowledge Base**. The model owns stable nonzero **Canonical Form** ids, dense row mappings, aliases, operand roles, syntax and semantic families, and tool capability status. Assembler, decoder, disassembler, simulator, sample generation, and coverage become **Generated Tool Views** over that model.

## User Stories

1. As a tooling maintainer, I want one canonical form id across all M68K tools, so that assembler and decoder parity can be checked directly.
2. As a tooling maintainer, I want nullable form ids separated from dense array rows, so that row zero cannot be confused with "no form".
3. As a tooling maintainer, I want aliases represented in generated metadata, so that runtime code does not hand-roll canonicalization.
4. As a tooling maintainer, I want operand roles and syntax families generated once, so that corpus and renderer code consume shared facts.
5. As a tooling maintainer, I want generated lookup aids keyed by canonical form id, so that runtime code stops scanning all forms.
6. As a tooling maintainer, I want decode candidates expressed as canonical form ids, so that disassembly does not own a parallel identity.
7. As a tooling maintainer, I want ambiguous decode ties rejected before runtime selection, so that ambiguity is a metadata failure.
8. As a tooling maintainer, I want tests proving form id uniqueness and row mapping, so that the identity contract stays stable.

## Implementation Decisions

- Use `M68kFormId` as a nullable identity where `0` means no form.
- Use a separate dense row type for generated table storage.
- Use a separate operand slot type where the no-slot sentinel is distinct from valid slots.
- Emit a shared generated form table before tool-specific views.
- Make assembler and disassembler generators consume canonical form ids rather than creating independent form identities.
- Generate mnemonic-to-form ranges, canonical-id-to-tool-row mappings, and decode buckets from the model.
- Pre-sort decoder candidates by generated specificity and fail generation or strict coverage on ambiguous equal-specificity candidates.

## Testing Decisions

- Test identity contracts with generated data: nonzero ids, uniqueness, id-to-row mapping, row-to-id mapping, and sentinel separation.
- Test assembler resolve-to-encode through canonical form id.
- Test decoder results carry canonical form id.
- Test disassembler rendering uses canonical form metadata rather than private form repair.
- Test ambiguity rejection at generation or strict coverage boundary.

## Out of Scope

- Full generated sample-plan replacement; that belongs to PRD 025.
- Full simulator/effect migration; that belongs to PRD 026.
- Implementing deferred unsupported instruction families.
- Preserving old generated table shapes for compatibility.

## Acceptance Criteria

- One generated canonical form inventory exists.
- Assembler and disassembler tool views reference canonical form ids.
- Runtime result state carries canonical form id where form identity is needed.
- Dense table rows are not used as nullable identities.
- Runtime whole-form scans by mnemonic and operand shape are removed or isolated behind generated candidate ranges.
- Decoder candidates are canonical form ids sorted by generated specificity.

## Deletion / Cleanup Expectations

- Delete split assembler/disassembler form identity paths as callers migrate.
- Delete runtime joins from disassembler-private forms back to assembler forms.
- Delete fallback resolver scans made redundant by generated lookup aids.

## Verification

- Run generator tests.
- Run C assembler, disassembler, and instruction-spec tests.
- Run asm -> decode parity tests for sampleable forms available before PRD 025 completes.

## Open Questions

- None. The proposal explicitly rejects compatibility-preserving migration as a long-term goal.
