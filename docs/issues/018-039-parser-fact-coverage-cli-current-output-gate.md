# 018-039: Parser Fact Coverage CLI Current Output Gate

Status: completed

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

Completed behavior:

- `coverage` with no `--parser-output` now fails with an explicit diagnostic
  instead of producing a passing empty closeout report.
- `coverage --allow-empty` preserves explicit inventory/report-only output.
- `coverage --current-macos-c-backend` loads the committed MPW fixture through
  the Mac C backend and checks the current parser-emitted fact refs.
- Invalid accepted claims still fail closed.
- Mac byte-entry and relocation/fixup remain candidate/deferred.

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

- [x] Coverage CLI behavior checked.
- [x] In-memory coverage API tests checked.
- [x] Mac C backend summary fact output checked.
- [x] Invalid accepted-claim failure checked.
- [x] Second-pass review checked that no empty-output success remains in the
  closeout proof path.

## Research Review

- [x] Empty coverage no longer satisfies closeout validation.
- [x] Current Mac parser output is covered by CLI or documented closeout command.
- [x] Candidate/deferred Mac facts remain non-accepted.
- [x] Proposal 018 closeout text matches the implemented command.

## Required Sign-Off

- [x] `uv run python -m amiga_reversing.tools.platform_executable_formats coverage`
  behavior is explicitly tested and documented.
- [x] Platform executable format tests pass.
- [x] Targeted Mac C backend tests pass.
- [x] `git diff --check` passes.

## Completion Evidence

- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage`
  returned failure for empty closeout input.
- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage
  --allow-empty` passed as explicit inventory output.
- `uv run python -m amiga_reversing.tools.platform_executable_formats coverage
  --current-macos-c-backend` passed and checked current Mac C backend output.
- `uv run python -m pytest tests/test_platform_executable_formats.py -q`
  passed.
- `uv run python -m pytest tests/test_macos_c_backend.py -q` passed.
- `git diff --check` passed.
