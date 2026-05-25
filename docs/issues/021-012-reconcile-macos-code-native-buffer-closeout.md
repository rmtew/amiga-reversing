# 021-012: Reconcile Mac CODE Native Buffer Closeout

Status: active

## Proposal

Proposal: `docs/proposals/021-native-macos-code-source-pipeline.md`

## Context

Proposal 021 is complete for its main native Mac CODE source pipeline, but the
post-closeout buffer cleanup needs final documentation after 021-009 through
021-011. The proposal should describe the final state without stale blocker
language or hidden `amiga-raw` caveats.

## What to build

Update Proposal 021 so it is cohesive after the native flat buffer cleanup:

- selected Mac CODE listing and preview paths use native Mac CODE identity;
- the low-level in-memory buffer path is neutral/non-Amiga;
- any generic M68K internals are explicitly platform-neutral;
- Mac byte-entry, relocation/fixup, source-to-CODE, and non-CODE resource facts
  remain deferred or candidate under Proposal 018 authority.

Do not reopen unrelated Mac executable semantics.

## Acceptance criteria

- [ ] Proposal 021 contains no stale wording saying candidate preview rendering
      still uses `RawBinarySource`.
- [ ] Proposal 021 contains no stale wording implying the Mac CODE C buffer
      artifact still depends on `amiga-raw`.
- [ ] Proposal 021 records 021-009, 021-010, and 021-011 outcomes.
- [ ] The issue ordering and final future-work sections match the implemented
      state.
- [ ] All completed 021 issue files in this batch are deleted after their work
      is committed.
- [ ] No source behavior changes are bundled into this docs closeout issue.

## Verification

Run at minimum:

```powershell
git diff --check
```

## Blocked by

- `docs/issues/021-011-guard-macos-code-raw-identity-leaks.md`
