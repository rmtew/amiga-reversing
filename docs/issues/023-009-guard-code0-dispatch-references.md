# 023-009: Guard CODE 0 Dispatch References

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 was closed for Mac source presentation, but closeout review found
  one source-reference accuracy bug.
- C currently emits a validated `code0_dispatch_reference` for every nonzero
  CODE resource.
- The MPW `Asm` artifact shows many resources with `jt_first=65535 jt_count=0`
  while also showing validated CODE 0 dispatch references. That overstates
  accepted routing evidence.

## What To Build

Guard CODE 0 dispatch source references in the C-owned Mac restored-source
packet.

Emit a validated `code0_dispatch_reference` only when the parsed resource has an
actual CODE 0 jump-table span:

```text
first_jump_table_entry_offset != 0xffff
jump_table_entry_count > 0
```

When no span exists, either omit the dispatch reference or emit a typed
deferred/unlinked placeholder. Do not emit accepted/validated routing for absent
evidence.

## Acceptance Criteria

- [ ] Validated `code0_dispatch_reference` requires a real nonzero jump-table
      span.
- [ ] Resources with `jt_first=65535 jt_count=0` do not show validated CODE 0
      dispatch references in artifact/API output.
- [ ] At least one real dispatch-span case remains covered.
- [ ] Tests fail if absent spans are promoted to accepted routing.
- [ ] Proposal 023 records the corrected behavior.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [ ] Focused Mac C/backend/project/artifact tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `cmd /c src\precommit.bat` passes if shared C/source output changes.
- [ ] `git diff --check` passes.
