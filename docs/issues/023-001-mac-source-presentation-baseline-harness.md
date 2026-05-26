# 023-001: Mac Source Presentation Baseline Harness

Status: active
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 starts after 020/021/022 completed shared executable import,
  native Mac CODE identity, and C-owned restored-source authority.
- This issue establishes an executable baseline harness for the committed MPW
  `Asm` Mac fixture.
- The harness must prove the user-visible source presentation boundary, not just
  print an inventory.

## What To Build

Add tests and/or a narrow command/API proof that enumerates current Mac source
presentation through C-owned restored-source surfaces and fails closed if core
evidence disappears.

The proof must cover:

- CODE resource inventory for the fixture;
- selected and non-selected CODE resource presentation status;
- restored-source packet presence or explicit typed deferred placeholder;
- source ownership verifier status;
- source reference records;
- executable resource placeholders;
- web/API/artifact visibility of the same evidence.

## Acceptance Criteria

- [ ] The baseline proof runs against the committed MPW `Asm` fixture.
- [ ] It checks C-owned restored-source packets, not Python-synthesized success.
- [ ] It fails if an executable CODE resource is neither rendered nor represented
      by a typed deferred source placeholder.
- [ ] It fails if verifier state, source references, or placeholders disappear
      from artifact/web/API presentation.
- [ ] It records the next implementation blocker in Proposal 023 without
      reclassifying candidate/deferred facts.
- [ ] No Mac round-trip claim is introduced.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [ ] Proposal 023 context checked before work.
- [ ] Focused Mac tests pass.
- [ ] Platform executable validate/coverage pass.
- [ ] `git diff --check` passes.
