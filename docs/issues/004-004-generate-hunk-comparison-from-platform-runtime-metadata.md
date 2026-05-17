# 004-004 Generate HUNK Comparison From Platform Runtime Metadata

Status: Implemented
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

`src/platform_amiga_hunk.c` consumes generated HUNK runtime metadata, but
`src/m68k_reproduction_compare.c` still hardcodes HUNK ids, relocation
classification, section detection, and skippable record categories.

That duplicates platform format knowledge downstream from
`knowledge/amiga_hunk_file.json`.

## Scope

Move reproduction comparison onto generated HUNK helpers.

Expected helper coverage:

- record id lookup
- load-file validity
- section/data/bss classification
- debug/symbol/ext/relocation skippable classification
- relocation record kind/width classification

Delete local hardcoded HUNK constants and classification switches from
`src/m68k_reproduction_compare.c` once generated helpers cover them.

## Acceptance Criteria

- Reproduction comparison uses generated platform-format metadata for HUNK
  record decisions.
- Local HUNK id constants in `src/m68k_reproduction_compare.c` are removed
  unless they are purely test fixture bytes.
- Generated helper tests cover the record categories used by reproduction
  comparison.
- Existing HUNK comparison behavior is preserved for supported records.

## Non-Goals

- Implement `HUNK_OVERLAY`.
- Change binary comparison policy.
- Add fallback handling for unknown records.

## Verification

```text
regenerate platform format runtime artifacts if generator changes
focused HUNK metadata/helper tests
focused reproduction comparison tests
cmd /c src\precommit.bat
```

## Implementation Notes

- `src/m68k_reproduction_compare.c` now uses generated
  `amiga_hunk_file_runtime` lookup helpers for HUNK ids, section starts,
  terminators, relocations, EXT variants, and payload-vs-BSS classification.
- Local HUNK record id constants were removed from reproduction comparison.
- Added a C metadata test covering the generated categories used by
  reproduction comparison.
- Existing precommit suite passes.
