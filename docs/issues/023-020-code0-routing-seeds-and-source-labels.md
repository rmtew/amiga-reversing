# 023-020: CODE 0 Routing Seeds And Source Labels

Status: complete

Proposal: `docs/proposals/023-classic-mac-os-source-presentation.md`

Depends on: `023-018`

## Problem

CODE 0 routing is visible as context, but it is not yet doing enough work for
source reconstruction. Valid routing evidence should seed labels and candidate
entry relationships; absent spans must remain unlinked.

Local docs support CODE 0 as jump-table/application metadata and CODE 1 as the
main segment convention. The worker should use that documented structure instead
of treating CODE 0 routing as an unknown blocker.

CODE 0-derived labels may be generated labels. Original segment/routine names
are used only where resource names or source evidence directly support them.

## Required Work

- Use documented CODE 0 and segment map structure to create source labels and
  candidate entry seeds only where a real table/span exists.
- Generated source labels are sufficient for accepted routing/xref presentation.
- Keep CODE 0 bytes themselves as structured metadata/data unless an explicit
  executable span is identified.
- Keep absent spans such as `jt_first=65535 jt_count=0` unlinked/deferred.
- Render valid CODE 0 links in `Asm.s`, API, and web source sections as
  labels/xrefs, not only report prose.
- Keep CODE 0 metadata/data separate from executable CODE body disassembly.

## Acceptance

- [x] Linked CODE resources have stable labels and visible xrefs from CODE 0 source
  context.
- [x] Absent-link resources do not get fake accepted dispatch references.
- [x] Tests cover a linked CODE resource, an absent-link CODE resource, and the
  generated artifact labels/xrefs.

## Result

- CODE 0 jump-table rows now produce `generated_code0_routing_xref` records only
  when the target CODE resource has a real executable span.
- Routine offsets are translated through the target CODE body range, so
  far-model headers remain metadata/data and do not receive fake routing labels.
- Source sections expose both the CODE 0 generated routing xrefs and target
  `incoming_code0_xrefs`; `Asm.s` and the web source panel render the same
  relationships.
- Current MPW evidence resolves CODE 0 entry 0 to CODE 27 payload offset 204.
  Resources without resolvable real spans, such as CODE 19 in the current
  fixture, remain unlinked.

## Verification

```powershell
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend --current-amiga-hunk --current-atari-prg
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py tests\test_web_app_source.py -q
cmd /c src\precommit.bat
git diff --check
```
