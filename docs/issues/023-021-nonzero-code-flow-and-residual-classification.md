# 023-021: Nonzero CODE Flow And Residual Classification

Status: active

Proposal: `docs/proposals/023-classic-mac-os-source-presentation.md`

Depends on: `023-019`, `023-020`

## Problem

Nonzero CODE resources are visible, but their executable bodies are still mostly
undifferentiated byte rows. A reverser needs reachable instructions, labels,
xrefs, data rows, and narrow residuals.

CODE 1 is the required first proof because local docs and current parser output
identify it as the `Main` segment with a far-model header and executable body
after payload offset 40.

The expected result is Amiga/Atari-level auto-analysis: decoded instructions,
generated labels, xrefs, data/metadata/residual splits, and known platform/trap
annotations. Human-quality names and comments are later reversing work.

## Required Work

- Follow executable code inside nonzero CODE resources from documented entry
  evidence, CODE 0 seeds, known entry/stub patterns, branch/call targets, and
  decoder fallthrough.
- Start with CODE 1 and then extend the same model to other nonzero CODE
  resources whose segment header and decoder results support source rows.
- Emit stable labels and xrefs for branch, call, jump, and data-reference
  targets.
- Use generated names when no source/platform evidence provides a meaningful
  symbol.
- Render data discovered from instruction references as data rows rather than
  candidate code bytes.
- Record attempted entry evidence and decode result for each nonzero CODE
  resource, including resources without accepted entry evidence.
- Keep unsupported spans as exact typed residuals with reason and next required
  implementation.
- Do not use missing original source symbols, A5 lifetime proof, or Segment
  Loader fixup decoding as a reason to avoid rendering decoder-supported
  instruction rows.
- Do not use lack of human semantic naming as a reason to leave decoded code as
  bytes.

## Acceptance

- CODE 1 contains real instruction rows and recovered labels/xrefs for the
  currently supported path.
- CODE 1 no longer presents the whole candidate body as one byte-real block.
- Unsupported spans remain visible as precise residuals, not broad orphan or
  candidate buckets.
- Tests cover instruction rows, labels/xrefs, data rows where discovered, and
  residual accounting.

## Verification

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
cmd /c src\precommit.bat
git diff --check
```
