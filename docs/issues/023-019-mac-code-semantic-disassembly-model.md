# 023-019: Mac CODE Semantic Disassembly Model

Status: active

Proposal: `docs/proposals/023-classic-mac-os-source-presentation.md`

Depends on: `023-018`

## Problem

Mac CODE resources are now byte-visible, but CODE body bytes are not being
restored as M68K source. This leaves the reverser with large `dc.b` blocks
instead of instruction/data rows.

Local docs already support starting this implementation. They establish CODE
resources as executable source containers, CODE 1 as the main segment
convention, and documented near/far segment headers. Proposal 024 records that
far-model code follows the 40-byte header and that the current MPW fixture has
zero documented relocation offsets, so fixup decoding is not a prerequisite for
the first semantic disassembly slice.

This issue does not need human semantic naming. Generated labels and mechanical
xrefs are the expected output for auto-analysis.

## Required Work

- Feed classifiable Mac CODE body spans from the native C Mac CODE path into the
  shared M68K disassembly machinery.
- Start with supported nonzero CODE body spans: far-model body at payload offset
  40, near-model body at payload offset 4.
- Do not reintroduce raw-file compatibility transports or Python-synthesized
  authority.
- Keep far-model segment headers, CODE 0 metadata, padding, and non-instruction
  structures as typed data/metadata.
- Emit C-owned source rows for decoded instructions with CODE resource identity,
  payload offset, bytes, size, rendered text, flow classification, and
  provenance.
- Emit generated labels for auto-discovered entrypoints, branch targets, call
  targets, data references, and residual placeholders.
- Emit exact typed residual rows for invalid/unsupported spans.
- If a specific CODE span still cannot be disassembled, record the exact failed
  evidence path and continue with other supported spans.

## Acceptance

- CODE 1 entry/stub bytes render as instruction rows where the decoder accepts
  them.
- Instruction rows can use generated labels; meaningful routine names are not
  required.
- CODE 1 far-model header remains metadata/data, not fake code.
- The artifact, API, and web payload consume the same C-owned row model.
- Tests fail if the supported CODE 1 executable span regresses to only `dc.b`.

## Verification

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
cmd /c src\precommit.bat
git diff --check
```
