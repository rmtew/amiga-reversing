# M68K Diagnostic Coverage Manifest

Status: Ready for issue execution
Source proposal: `docs/proposals/005-m68k-generated-coverage.md`
Created: 2026-05-16
Supersedes: None

## Problem Statement

Generated M68K form coverage is not visible enough. The assembler corpus can silently skip forms, assembler and disassembler form inventories diverge, and unsupported state is mixed with missing sample strategy.

## Solution

Add a short-lived diagnostic coverage manifest over the current generated assembler and disassembler tables. It must classify every current form, report asm/disasm parity, record sample status, and fail strict mode for unclassified forms.

This is a bootstrap artifact only. It must be deleted or folded into the **Canonical Form Model** once that model owns the same classifications.

Diagnostic reporting and checks must use the shared coverage command surface:

```powershell
uv run python -m amiga_reversing.tools.m68k_coverage report --phase diagnostic
uv run python -m amiga_reversing.tools.m68k_coverage check --phase diagnostic
```

## User Stories

1. As a tooling maintainer, I want every generated form classified, so that missing coverage cannot hide behind silent skips.
2. As a tooling maintainer, I want asm/disasm inventory differences reported, so that the rewrite starts from measured facts.
3. As a tooling maintainer, I want missing sample strategies reported separately from intentionally unsupported forms, so that each failure has the right owner.
4. As a tooling maintainer, I want strict mode to fail on unclassified forms, so that coverage cannot regress silently.
5. As a tooling maintainer, I want report mode to be readable without opening test code, so that coverage state is inspectable during migration.
6. As a tooling maintainer, I want bootstrap diagnostic code to have explicit deletion criteria, so that it does not become a second form model.

## Implementation Decisions

- Build the diagnostic manifest from existing generated assembler and disassembler metadata.
- Classify forms by tool presence, sample status, asm/disasm match state, and unsupported status.
- Replace silent corpus skips with recorded manifest entries.
- Treat `missing_sample_strategy` as failing in strict mode.
- Allow report-only mode for current-state inventory before strict mode is enabled in CI.
- Expose report and check behavior through `amiga_reversing.tools.m68k_coverage`; do not add separate coverage commands to corpus-generation scripts.
- Keep the diagnostic manifest separate from the future **Canonical Form Model** and mark its removal conditions directly in docs and tests.

## Testing Decisions

- Test classification behavior, not the internal shape of the manifest implementation.
- Add or update tests that prove silent skipped forms become manifest entries.
- Add strict-mode tests for unclassified forms and missing sample strategies.
- Add report snapshot or structured-output tests that prove asm/disasm mismatch totals are surfaced.
- Reuse existing generated corpus and C backend test patterns where possible.

## Out of Scope

- Creating the final **Canonical Form Model**.
- Replacing assembler or disassembler generated table shapes.
- Implementing MOVE16, FSAVE/FRESTORE, PMMU, or generic coprocessor families.
- Adding simulator semantics coverage beyond reporting current status.

## Acceptance Criteria

- Every current assembler and disassembler form is represented in the diagnostic manifest.
- Silent sample skips are recorded with a concrete reason.
- Strict mode fails on unclassified forms.
- Report mode prints assembler counts, disassembler counts, matched counts, unmatched counts, sample status counts, and unsupported counts.
- Report and strict checks are available through `uv run python -m amiga_reversing.tools.m68k_coverage ... --phase diagnostic`.
- The diagnostic manifest has explicit deletion criteria tied to the **Canonical Form Model**.

## Deletion / Cleanup Expectations

- Delete or fold this diagnostic path into canonical-model reporting once PRD 024 and PRD 025 provide the same classifications.

## Verification

- Run the relevant Python tests for corpus generation and coverage reporting.
- Run C backend assembler/disassembler tests affected by generated metadata.
- Generate a coverage report and inspect counts for current known asm/disasm divergence.

## Open Questions

- None for initial implementation; exact report formatting can follow the codebase's existing generated-report conventions.
