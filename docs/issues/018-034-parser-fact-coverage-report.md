# 018-034: Parser Fact Coverage Report

Status: active

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-033-platform-executable-generated-fact-table.md`
- Purpose: report parser-emitted executable-format facts against the KB so
  accepted, candidate, deferred, unsupported, and invalid claims are visible in
  one place.

## Knowledge Delta

No new platform facts are required. This issue adds coverage reporting over
existing facts and parser output.

The report should answer:

- which parser-emitted facts are accepted and parser-consumable;
- which emitted facts are candidate/deferred/unsupported and therefore not
  accepted authority;
- which emitted facts are missing from the KB or have invalid parser-use state;
- which platform/parser areas are unreported.

## Default Behavior

No default target parsing or rendering behavior changes. This is a report and
validation surface. If any parser output is found invalid, fail closed in tests
or report blockers rather than silently accepting it.

## Evidence Standard

The report must be generated from current parser output and current KB-derived
fact metadata. Hardcoded pass lists are not acceptable except as explicit test
fixtures.

## Implementation Slice

AFK slice:

- add or extend a CLI/report command for parser fact coverage;
- include Mac current parser output;
- include Amiga/Atari coverage if current parser outputs are available without
  broad parser rewrites;
- add tests that reject unknown accepted claims and candidate-as-accepted
  promotions;
- update Proposal 018 with the resulting gap summary.

## Research Completion Standard

Complete only after checking all current parser fact producers found by repo
search and doing a second-pass review for missed emitted fact ids.

## Research Coverage

- [ ] Mac parser fact producers checked.
- [ ] Amiga parser fact producers checked or explicitly recorded as absent.
- [ ] Atari parser fact producers checked or explicitly recorded as absent.
- [ ] Platform executable KB facts checked through generated table.
- [ ] Second-pass search for emitted fact id strings completed.

## Research Review

- [ ] Coverage report distinguishes accepted from candidate/deferred output.
- [ ] Invalid fact ids fail tests or produce explicit blockers.
- [ ] Report does not mutate target state or generated source.
- [ ] Proposal 018 records remaining coverage gaps.

## Required Sign-Off

- [ ] Coverage command/report test passes.
- [ ] Platform executable format tests pass.
- [ ] Relevant parser/listing tests pass.

