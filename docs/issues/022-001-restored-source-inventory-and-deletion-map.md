# 022-001: Restored Source Inventory And Deletion Map

Status: active

## Proposal

Proposal: `docs/proposals/022-platform-executable-kb-display-pipeline.md`

## What to build

Research the current Amiga HUNK, Atari ST PRG, and Mac CODE source/listing,
artifact, web/API, ownership, reference, relocation, and verifier paths. This is
a bounded implementation inventory, not a blocker report.

The result must be a concrete replacement/deletion map for Proposal 022.

## Investigation anchors

Trace at minimum:

- `src/platform_executable_summary.h`
- `src/m68k_render_plan.h`
- `src/platform_file_json.c`
- `src/platform_file_lib.c`
- `src/m68k_analysis_facts_v2.c`
- `src/m68k_render_ir.c`
- `amiga_reversing/disasm/c_backend.py`
- `amiga_reversing/disasm/reproduction.py`
- `amiga_reversing/disasm/macos_project_payload.py`
- `amiga_reversing/disasm/macos_target_artifact.py`
- `amiga_reversing/disasm/macos_web_view.py`
- `amiga_reversing/web/app.js`

## Acceptance criteria

- [ ] Current ownership/range sources are listed for Amiga, Atari, and Mac.
- [ ] Current relocation/reference sources are listed for all three platforms.
- [ ] Current source/listing/artifact/web/API consumers are listed.
- [ ] Legacy fields and paths that duplicate the future restored source model
      are listed with required replacement proof.
- [ ] Existing C render-plan row metadata and listing artifact APIs are mapped
      to the restored source model.
- [ ] Mac compatibility fields (`selected_code_segment`, `code_layout`,
      `orphan_ranges`, `relocation_fixups`, `code_segment_map`,
      `preview_windows`, `non_code_resource_details`) are mapped to replacement
      restored source records.
- [ ] Round-trip proof surfaces for Amiga/Atari are listed.
- [ ] Mac no-round-trip/source-quality proof surfaces are listed.
- [ ] The first coding boundary for 022-002 is explicit.
- [ ] Proposal 022 is updated with any unexpected constraints or future UI
      follow-up observations.

## Verification

Run:

```powershell
git diff --check
```

## Blocked by

None - can start immediately.
