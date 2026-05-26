# 023-012: All-CODE Source Body Sections

Status: complete
Type: AFK
Source proposal: docs/proposals/023-classic-mac-os-source-presentation.md

## Proposal Context

- Proposal 023 requires every executable CODE resource to be visible as source or
  as a typed source-visible placeholder.
- Current evidence says the MPW `Asm` fixture has many CODE resources, but the
  artifact remains effectively selected-CODE-centric.
- 023-011 establishes the source-first artifact shell this issue must fill.

## What To Build

Render every executable CODE resource in the MPW `Asm` target as a visible
source-body section. Fully covered CODE resources should render restored-source
rows. Deferred, partial, or unsupported CODE resources must still render stable
placeholder/data sections with resource id, status, reason, and byte span.

Do not promote candidate/deferred facts to accepted semantics just to make the
section prettier.

Do not treat an undecoded CODE resource as a blocker. Use the local Mac docs and
formal KB to classify the resource structure as far as the bytes permit. If code
entry/lifetime semantics remain unproven, still emit a conservative section that
preserves the bytes and labels the exact unproven semantic.

## Acceptance Criteria

- [x] Every CODE resource in the current MPW `Asm` resource inventory has a
      visible section label or typed placeholder section in `Asm.s`.
- [x] Full/partial/deferred section status is visible in the source body.
- [x] Deferred sections preserve bytes or explicit source-visible placeholders
      instead of disappearing into report comments.
- [x] For every deferred/partial section, the implementation records what local
      Mac documentation/KB rule was applied and what exact semantic remains
      unproven.
- [x] Tests compare the CODE resource inventory against source-body section
      identities.
- [x] No selected-CODE-only path is treated as complete program source.

## Completed Result

- `Asm.s` now has a source-body section for every current MPW `Asm` CODE
  resource before the supporting-evidence report.
- CODE 1 retains the full selected listing. Other CODE resources expose exact
  C-owned payload/layout ranges, status, fact/parser-use evidence, byte-preserving
  placeholders, and bounded preview rows where the model provides them.
- The artifact test compares the C-backed CODE inventory against source-body
  section identities and fails if the output returns to selected-CODE-only
  source coverage.

## Blocked By

- docs/issues/023-011-source-first-asm-artifact-contract.md

## Required Sign-Off

- [x] Focused Mac artifact/project/API tests pass.
- [x] Platform executable validate/coverage pass with Mac/Amiga/Atari current
      backends.
- [x] `cmd /c src\precommit.bat` passes if shared rendering or C code changes.
- [x] `git diff --check` passes.
