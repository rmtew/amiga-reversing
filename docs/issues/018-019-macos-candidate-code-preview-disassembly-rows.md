# 018-019: Mac OS Candidate CODE Preview Disassembly Rows

Status: open

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

## Research Coverage

- [ ] Current selected CODE listing adapter traced.
- [ ] Current preview row generation traced.
- [ ] Safe bounded decode policy selected.
- [ ] Fallback policy selected.
- [ ] Artifact/web impact checked.
- [ ] 012/018 wording checked before implementation.

## Research Review

- [ ] Second pass checked decoded rows are bounded to candidate ranges.
- [ ] Candidate rows are not labelled accepted.
- [ ] Fallback rows remain available with reason.
- [ ] CODE 0 remains metadata-only.
- [ ] Selected CODE 1 listing still works.
- [ ] Deferred relocation/fixup state remains visible.
- [ ] Proposal 012/018 docs updated.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] Decoded candidate preview rows added where safe.
- [ ] Data-row fallback preserved with explicit reason.
- [ ] Preview rows remain bounded to candidate code ranges.
- [ ] Candidate/deferred facts are not promoted to accepted output.
- [ ] MPW `Asm` artifact regenerated if output changes.
- [ ] Relevant payload/artifact/web tests pass.
- [ ] CDP browser verification passes if web output changes.
- [ ] `amiga_reversing.tools.platform_executable_formats validate` passes.
- [ ] `amiga_reversing.tools.validate_018_issues` passes.
- [ ] Post-commit review found no unresolved worthwhile findings.
