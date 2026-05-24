# 018-039: Parser Fact Coverage CLI Current Output Gate

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Reopens a closeout finding from 018-034/018-038 review.
- Problem: `amiga_reversing.tools.platform_executable_formats coverage` exits
  successfully with no parser outputs and reports all platforms/records as
  unreported. Proposal 018 closeout says parser fact coverage is a current gate,
  but the CLI can currently pass without checking current parser output.
- This issue must not reopen Mac byte-entry or relocation/fixup as accepted
  facts.

## Knowledge Delta

No new executable-format facts are expected. The change is to make coverage
validation match the already-recorded KB authority:

- accepted facts stay accepted only where the KB says so;
- candidate/deferred/unsupported facts remain non-accepted;
- Mac byte-entry and relocation/fixup remain candidate/deferred.

## Default Behavior

The coverage CLI must not silently pass an empty current-output check.

Acceptable outcomes:

- default `coverage` includes a real current Mac parser output fixture/report and
  validates it; or
- default `coverage` fails with an explicit diagnostic unless `--parser-output`
  is supplied; plus an explicit `--allow-empty` or equivalent exists only for
  inventory/report-only use.

Preferred outcome: provide a command path that can be used in closeout
validation without extra temp-file plumbing and proves current Mac C backend
output.

## Evidence Standard

Tests must prove:

- empty coverage is not mistaken for closeout validation;
- current Mac parser output is checked by a real CLI/API path;
- invalid accepted claims still fail closed;
- unreported Amiga/Atari parser outputs remain visible until those parsers emit
  KB fact metadata.

## Implementation Slice

AFK slice:

- inspect `platform_executable_formats coverage` and its tests;
- add a real current-output coverage path or make empty input fail explicitly;
- update tests to cover the chosen behavior;
- update Proposal 018 closeout wording if the exact command changes;
- do not change parser fact states except to correct reporting of existing
  current output.

## Research Completion Standard

Complete only after checking both CLI behavior and in-memory API behavior. The
worker must verify that the command used as closeout proof cannot pass with no
parser output by accident.

## Research Coverage

- [ ] Coverage CLI behavior checked.
- [ ] In-memory coverage API tests checked.
- [ ] Mac C backend summary fact output checked.
- [ ] Invalid accepted-claim failure checked.
- [ ] Second-pass review checked that no empty-output success remains in the
  closeout proof path.

## Research Review

- [ ] Empty coverage no longer satisfies closeout validation.
- [ ] Current Mac parser output is covered by CLI or documented closeout command.
- [ ] Candidate/deferred Mac facts remain non-accepted.
- [ ] Proposal 018 closeout text matches the implemented command.

## Required Sign-Off

- [ ] `uv run python -m amiga_reversing.tools.platform_executable_formats coverage`
  behavior is explicitly tested and documented.
- [ ] Platform executable format tests pass.
- [ ] Targeted Mac C backend tests pass.
- [ ] `git diff --check` passes.

