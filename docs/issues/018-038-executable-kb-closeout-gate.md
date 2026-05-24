# 018-038: Executable KB Closeout Gate

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by:
  - `docs/issues/018-031-amiga-hunk-accepted-format-records.md`
  - `docs/issues/018-032-atari-prg-accepted-format-records.md`
  - `docs/issues/018-034-parser-fact-coverage-report.md`
  - `docs/issues/018-035-mac-blocked-fact-regression-gate.md`
  - `docs/issues/018-037-macos-blocker-resolution-or-final-deferral.md`
- Purpose: decide whether Proposal 018 is complete as the executable-format KB
  authority, and record any remaining work as explicitly out-of-scope or
  downstream.

## Knowledge Delta

No new facts should be introduced here. This is a closeout verification gate
over completed KB, generated fact, parser coverage, and downstream blocker
state.

## Default Behavior

No behavior changes unless the closeout audit finds a small stale report/test
claim that contradicts the completed KB state.

## Evidence Standard

Closeout requires current validation, not historical claims:

- KB validates;
- generated fact tables are fresh;
- parser fact coverage is clean or has explicit blockers;
- Mac byte-entry and relocation/fixup are accepted only if evidence supports
  them, otherwise formally deferred;
- Amiga and Atari first records have accepted/parser-asserted or explicitly
  deferred state;
- Proposal 012 dependency state is updated.

## Implementation Slice

AFK closeout slice:

- rerun all 018 validators and targeted tests;
- review Proposal 018 against current KB/report output;
- review Proposal 012 dependency text;
- update proposals with closeout or remaining blocked state;
- delete completed 018 issue files only if durable conclusions have been
  promoted into Proposal 018.

## Research Completion Standard

The worker must perform a full closeout audit, not rely on issue status labels.
Every dependency listed above must be checked by commit/content, not assumed.

## Research Coverage

- [ ] 018-031 result checked.
- [ ] 018-032 result checked.
- [ ] 018-034 parser coverage result checked.
- [ ] 018-035 Mac blocked-fact gate checked.
- [ ] 018-037 Mac final KB state checked.
- [ ] Proposal 012 downstream state checked.
- [ ] Second-pass closeout contradiction review completed.

## Research Review

- [ ] No historical issue claim is used without current validation.
- [ ] All completed issue conclusions are promoted to Proposal 018 before issue
  deletion.
- [ ] Proposal 012 is either unblocked for a named next issue or explicitly
  still blocked with exact reason.
- [ ] No broad artifact/source churn was committed as closeout noise.

## Required Sign-Off

- [ ] Platform executable KB validation passes.
- [ ] Parser fact coverage report passes or reports explicit accepted blockers.
- [ ] Targeted Mac/Amiga/Atari parser tests pass.
- [ ] `git diff --check` passes.

