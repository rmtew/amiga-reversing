# 012-027: Mac Target Current Proof Rerun

Status: active

## Proposal Context

- Source proposal: `docs/proposals/012-classic-mac-os-m68k-platform.md`
- Parallel-safe after `012-025` starts.
- Purpose: rerun the current Mac platform proof after Proposal 018 closeout and
  fix only stale proof/test/doc drift.

## Scope

Prove the current starter Mac target state:

- platform executable KB validates;
- parser fact coverage checks current Mac C backend output;
- Mac project payload opens through the normal project path;
- committed Mac target artifact drift check passes;
- Mac listing surface does not emit Amiga `SECTION code,code`;
- candidate/deferred labels remain visible for byte-entry and relocation/fixup
  state.

## Out of Scope

- Do not implement byte-entry or relocation/fixup semantics.
- Do not regenerate artifacts for cosmetic churn.
- Do not rename labels or alter source output unless a proof failure requires it.
- Do not touch Proposal 018 except if a broken reference in Proposal 012 proof
  text needs correction.

## Files Likely Touched

- Tests only if stale.
- Proposal 012 only to record current proof evidence.
- Mac target artifact only if a drift test proves the committed artifact is
  stale.

## Acceptance Criteria

- [ ] Current proof commands are run and recorded.
- [ ] Any failures are fixed narrowly or recorded as blockers for `012-026`.
- [ ] Candidate/deferred Mac executable states remain non-accepted.
- [ ] No broad source/artifact churn is committed.
- [ ] Proposal 012 records the verified current proof state.

## Required Tests

Run:

```text
uv run python -m amiga_reversing.tools.platform_executable_formats validate
uv run python -m amiga_reversing.tools.platform_executable_formats coverage --current-macos-c-backend
uv run python -m pytest tests\test_platform_executable_formats.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py tests\test_macos_web_view.py -q
git diff --check
```

If browser/CDP-visible claims are changed, include the relevant CDP test.

## Cleanup / Deletion

Delete this issue after completion only after Proposal 012 records the proof
result.

## Notes for Agents

This issue should produce confidence, not new scope. A proof failure can create
a blocker; it should not cause broad Mac support redesign inside this issue.

