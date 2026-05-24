# 012-026: Mac Starter Scope Closeout

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Blocked by:
  - `docs/issues/012-025-post-018-closeout-blocker-map.md`
  - `docs/issues/012-027-mac-target-current-proof-rerun.md`
  - `docs/issues/012-028-mac-future-work-extraction.md`
- Proposal 018 is complete as the executable-format KB authority. Proposal 012
  must consume its accepted/deferred/unsupported states, not bypass them.

## Scope

Decide whether Proposal 012 can close as starter Classic Mac OS m68k platform
support.

Starter closeout may include:

- HFS/resource/CODE project visibility;
- Mac source/project payload support;
- Mac-style listing surface without Amiga `SECTION code,code`;
- current candidate/deferred labels for unresolved CODE byte-entry and
  relocation/fixup state;
- current target artifact drift/proof checks.

Starter closeout must not require:

- accepted nonzero CODE byte-entry rules;
- classic 68K CODE relocation/fixup implementation;
- source-to-CODE mapping without a matching built product;
- broad non-CODE payload decoding;
- MPW byte-for-byte roundtrip.

## Out of Scope

- Do not implement deferred executable facts.
- Do not broaden Mac resource decoding.
- Do not reopen Proposal 018.
- Do not keep 012 open for future research if the starter target is complete and
  the future work is explicitly recorded.

## Files Likely Touched

- `docs/proposals/012-classic-mac-os-m68k-platform.md`
- `docs/issues/012-026-mac-starter-scope-closeout.md`
- Possibly cleanup/delete completed `012-*` issue files after proposal
  promotion.

## Acceptance Criteria

- [ ] The proposal status is updated to either completed-for-starter-scope or
  explicitly still open with a concrete missing starter requirement.
- [ ] Future/deferred work remains visible and is not mistaken for starter
  acceptance.
- [ ] Required proof from `012-027` is referenced.
- [ ] Future work extraction from `012-028` is reflected.
- [ ] Completed issue files are deleted only after their durable conclusions are
  in Proposal 012.

## Required Tests

Run the proof commands established by `012-027`, at minimum:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend
uv run python -m pytest tests\test_platform_executable_formats.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py -q
git diff --check
```

If web-visible claims are updated, include the relevant web/CDP test.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 012 records the final
starter-scope closeout state.

## Notes for Agents

Formal deferral is valid. Do not convert deferred Mac executable facts into
accepted starter behavior. The closeout decision is about whether 012's starter
scope is satisfied while deeper correctness remains future work.

