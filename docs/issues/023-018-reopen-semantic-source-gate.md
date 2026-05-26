# 023-018: Reopen Semantic Source Gate

Status: complete

Proposal: `docs/proposals/023-classic-mac-os-source-presentation.md`

## Problem

The previous closeout allowed `passed_with_deferred_semantics` to close Proposal
023. That state proves byte preservation and visible residual accounting, but it
does not prove useful restored Mac source. The generated `Asm.s` can still render
CODE body spans as `dc.b` while the gate passes.

This is not blocked on broad Mac research. Local docs already support the first
semantic source slice: CODE resources carry executable code, CODE 0 is
jump-table/application metadata, CODE 1 is the main segment convention, and the
current far-model CODE parser identifies nonzero CODE body bytes after the
documented header.

The gate must distinguish mechanical source quality from human reversing
quality. 023 requires decoded assembly, generated labels, xrefs, typed ranges,
and platform context. It does not require meaningful routine names, original
source symbols, or high-level semantic comments.

## Required Work

- Keep Proposal 023 active.
- Rename or reclassify `passed_with_deferred_semantics` so it cannot be treated
  as final source-quality success.
- Split the gate into explicit statuses for byte preservation, source ordering,
  semantic disassembly progress, label/xref recovery, and residual unknowns.
- Treat stable generated labels/xrefs as sufficient for automated source
  presentation. Do not require human semantic names for gate success.
- Make semantic closeout fail when executable CODE body spans render only as
  byte-real rows.
- Update artifact/API/proposal wording so byte-real completion is a baseline,
  not a final source presentation result.
- Record that missing Segment Loader fixup decoding and A5 lifetime proof do not
  block semantic disassembly of current CODE body bytes with zero documented
  relocation offsets.

## Acceptance

- [x] A byte-real-only CODE body cannot pass the semantic closeout gate.
- [x] Tests cover the failed byte-real-only case.
- [x] Proposal 023 records the failed closeout cause and current active
      direction.
- [x] No Amiga/Atari coverage or exact gates are weakened.

## Completed Result

- `source_quality_gate.status` is now `byte_real_baseline`, with
  `baseline_status: passed_with_deferred_semantics` retained only as historical
  meaning.
- `source_quality_gate.semantic_closeout_status` is
  `blocked_byte_real_only` for the current artifact because executable CODE
  body spans still have zero semantic instruction rows.
- Gate output now separates byte preservation, source ordering, semantic
  disassembly progress, generated-label/xref recovery, and residual status.
- The artifact renders the reopened gate state before supporting evidence.
- Tests prove CODE 1's byte-real-only executable body cannot satisfy semantic
  closeout, while generated labels are accepted and human semantic names are
  explicitly not required.

## Verification

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
cmd /c src\precommit.bat
git diff --check
```
