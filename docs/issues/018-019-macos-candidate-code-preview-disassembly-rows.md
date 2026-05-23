# 018-019: Mac OS Candidate CODE Preview Disassembly Rows

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: Mac OS non-selected CODE preview usability
- Blocked by: `018-018`
- Work order: run before `018-020`, `018-023`, and `018-024` if those issues
  would touch Mac preview payload/artifact/web rendering.
- Current proposal state: non-selected CODE previews are visible in payload,
  artifact, and web UI, but preview rows are emitted as `dc.w`/`dc.b` data-style
  rows instead of decoded Mac-style m68k listing rows.
- Desired proposal state after this issue: bounded preview windows use decoded
  candidate m68k rows where the existing listing/decode path can safely produce
  them, with data-word fallback only when decode is unavailable or unsafe.

## Knowledge Delta

- Adds: decoded preview-row rendering requirements for candidate CODE previews.
- Changes: candidate previews become instruction-oriented where possible.
- Replaces: unconditional `dc.w`/`dc.b` preview rows for candidate code bytes.
- Deletes: no fallback rows; fallback remains required when decode fails.
- Leaves out of scope: accepted byte-entry validation, relocation/fixup
  interpretation, full non-selected listing routes, and roundtrip.

## Default Behavior

- Preview row decoding must stay bounded to existing candidate code ranges.
- Candidate preview rows remain `candidate_only`; no decoded instruction may be
  labelled accepted.
- Relocation/fixup state remains deferred and visible.
- CODE 0 remains metadata-only.
- Selected CODE 1 full listing remains unchanged.
- Any failed/unsafe decode falls back to data-word preview rows with a visible
  fallback reason.

## Evidence Standard

- Decoded preview rows must carry offset, bytes, text, range kind, fact id,
  fact status, parser-use value, and fallback/decode status.
- Tests must prove at least one non-selected preview uses decoded rows and at
  least one fallback path remains possible.
- Artifact and web UI must distinguish decoded candidate rows from fallback
  data rows.

## Implementation Slice

- Trace the current selected CODE listing adapter and identify the smallest
  reusable API for bounded preview decode.
- Extend preview window generation to request decoded rows from the existing
  Mac listing/decode path.
- Preserve current `dc.w`/`dc.b` fallback with explicit reason.
- Regenerate the MPW `Asm` artifact if output changes.
- Update the web UI only as needed to render decoded/fallback row status.
- Add focused payload/artifact/web/CDP tests.
- Update Proposal 012, Proposal 018, and `docs/platform-executable-formats.md`
  with the decoded preview state.

## Research Completion Standard

Record trace blocks for:

- selected CODE listing adapter reuse decision;
- preview decode API or helper added;
- fallback policy and exact reasons;
- decoded row fact/status propagation;
- tests proving candidate/deferred state is preserved.

## Research Notes

Trace blocks:

```text
Selected CODE listing adapter reuse:
  amiga_reversing.disasm.macos_listing_source already feeds selected CODE bytes
  into build_listing_artifact_profile_from_binary_source through a temporary
  RawBinarySource, then strips Amiga SECTION code,code from Mac-facing rows.

Preview decode helper:
  amiga_reversing.disasm.macos_project_payload now builds the same temporary
  raw local-offset source for bounded non-selected candidate preview bytes and
  consumes instruction/data rows from the shared listing artifact.

Fallback policy:
  Fallback dc.w/dc.b rows are emitted only when the preview is shorter than one
  m68k instruction word, decode raises, or decode produces no instruction rows.
  The row carries decode_status=fallback_data and a visible fallback_reason.

Fact propagation:
  Decoded and fallback rows inherit the candidate preview range fact
  macos.code_resource.movea_stack_a0.boundary.candidate, fact_status=candidate,
  and parser_use=candidate_only. Relocation/fixups remain deferred_only through
  the preview deferred_reasons list.
```

## Completion Evidence

```text
uv run python -m pytest tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_web_app_source.py -q
26 passed
node --check amiga_reversing\web\app.js
uv run python -m pytest tests\test_web_e2e_cdp.py::test_brave_cdp_macos_code_details_show_candidate_previews -q
1 passed
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.validate_018_issues
uv run ruff check amiga_reversing\disasm\macos_project_payload.py amiga_reversing\disasm\macos_target_artifact.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_web_app_source.py tests\test_web_e2e_cdp.py
All checks passed!
```

## Research Coverage

- [x] Current selected CODE listing adapter traced.
- [x] Current preview row generation traced.
- [x] Safe bounded decode policy selected.
- [x] Fallback policy selected.
- [x] Artifact/web impact checked.
- [x] 012/018 wording checked before implementation.

## Research Review

- [x] Second pass checked decoded rows are bounded to candidate ranges.
- [x] Candidate rows are not labelled accepted.
- [x] Fallback rows remain available with reason.
- [x] CODE 0 remains metadata-only.
- [x] Selected CODE 1 listing still works.
- [x] Deferred relocation/fixup state remains visible.
- [x] Proposal 012/018 docs updated.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] Decoded candidate preview rows added where safe.
- [x] Data-row fallback preserved with explicit reason.
- [x] Preview rows remain bounded to candidate code ranges.
- [x] Candidate/deferred facts are not promoted to accepted output.
- [x] MPW `Asm` artifact regenerated if output changes.
- [x] Relevant payload/artifact/web tests pass.
- [x] CDP browser verification passes if web output changes.
- [x] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [x] `amiga_reversing.tools.validate_018_issues` passes.
- [x] Post-commit review found no unresolved worthwhile findings.
