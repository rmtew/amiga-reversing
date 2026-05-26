# 023-022: Semantic Source Presentation Closeout

Status: active

Proposal: `docs/proposals/023-classic-mac-os-source-presentation.md`

Depends on: `023-018`, `023-019`, `023-020`, `023-021`

## Problem

Proposal 023 needs a real closeout gate. Byte-real visibility is useful
groundwork, but the desired outcome is Mac CODE source that is visibly useful to
a reverser: instructions, data, labels, xrefs, and precise residuals.

The closeout must be honest about remaining gaps. It may defer original source
symbol recovery, full source-to-CODE mapping, A5 lifetime/global-base proof,
Segment Loader fixup decoding for fixtures with nonzero relocation streams, and
resource-fork round-trip. It may not defer semantic disassembly of current CODE
body bytes merely because those larger gaps remain.

Closeout does not require intelligence-driven naming. Stable generated labels,
mechanical xrefs, decoded instructions, typed data/metadata/residual rows, and
known platform/trap annotations are the required automated output.

## Required Work

- Regenerate and review the committed MPW `Asm.s` artifact.
- Record before/after evidence showing which CODE resources moved from byte-real
  rows to semantic instruction/data/source rows.
- Require the source-quality gate to reach
  `semantic_source_complete_for_known_bounds`.
- Keep residual placeholders narrow, typed, justified, and linked to the next
  missing implementation.
- Mark Proposal 023 complete only if the artifact/API/web views all expose the
  semantic source model and no final claim rests on byte-real accounting alone.

## Acceptance

- `Asm.s` is source-first and contains real instruction/data rows for all
  supported executable spans.
- Generated labels/xrefs are present for auto-discovered control/data flow.
- CODE 0 routing, CODE 1 entry/body analysis, labels/xrefs, and residual
  accounting are covered by tests.
- Proposal 023 accurately distinguishes completed semantic source work from
  deferred Mac round-trip, resource-fork, Segment Loader, and A5 lifetime work.
- No completed issue is deleted until this final review confirms its acceptance
  evidence is present in the proposal.

## Verification

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
cmd /c src\precommit.bat
git diff --check
```
