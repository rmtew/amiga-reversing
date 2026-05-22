# 018-005: Mac OS Parser And Listing KB Migration

Status: open

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Knowledge area: applying accepted Mac executable facts to parser/listing code
- Blocked by: `018-003`, `018-004`
- Current proposal state: Mac parser/listing has useful foundation but its CODE
  boundaries are not guaranteed to come from cited KB facts.
- Desired proposal state after this issue: Mac CODE parser/listing behavior
  consumes or validates against accepted executable-format KB facts, and 012 can
  be reassessed on evidence rather than heuristics.

## Knowledge Delta

- Adds: KB-backed parser/listing behavior for Mac CODE resources.
- Changes: Mac CODE classification no longer treats candidate facts as accepted.
- Replaces: heuristic-only `movea.l (a7)+,a0` acceptance if not validated.
- Deletes: stale heuristic code only if the KB-backed path makes it obsolete.
- Leaves out of scope: byte-for-byte MPW roundtrip, complete non-CODE resource
  semantics, and unrelated target cleanup.

## Default Behavior

- Existing Amiga/Atari behavior must remain unchanged.
- Existing Mac project/API shape should remain stable unless KB-backed facts
  require an explicit schema update.
- Renderer output must label candidate/deferred ranges honestly.

## Evidence Standard

- Parser accepted code/data/entry classifications must point to validated or
  parser_asserted KB facts.
- Candidate facts may produce candidate ranges only.
- If KB facts are insufficient, fail closed or emit structured deferred output;
  do not invent accepted boundaries.

## Implementation Slice

- C parser: consume or validate against generated/platform executable facts.
- Python/API: expose fact ids/status in Mac summaries where useful.
- Renderer/listing: reflect accepted/candidate/deferred status.
- Tests: Mac fixture, negative candidate promotion, regression for no
  `SECTION code,code`, and unchanged Amiga/Atari behavior.
- Proposal: update 012 with the new evidence-backed status.

## Research Completion Standard

Record trace blocks for current Mac parser entrypoints, listing adapter,
generated metadata hook points, C/Python boundary, and obsolete code decisions.

## Research Coverage

- [ ] Current Mac C resource/CODE parser checked.
- [ ] Current Mac listing adapter checked.
- [ ] Generated KB/check hook point checked.
- [ ] Current heuristic code path checked.
- [ ] Existing tests and artifact drift checks checked.
- [ ] 012 closeout criteria checked.

## Research Review

- [ ] Second pass checked trace blocks against named files/functions.
- [ ] Candidate facts cannot produce accepted output.
- [ ] Renderer wording reviewed for overclaiming.
- [ ] Proposal 012 updated with evidence-backed status.

## Required Sign-Off

- [ ] Proposal context checked before implementation.
- [ ] 018-003 accepted Mac KB facts consumed or validated.
- [ ] 018-004 guardrails pass.
- [ ] Mac parser/listing tests pass.
- [ ] Existing Amiga/Atari tests remain unaffected or changes are justified.
- [ ] Stale heuristic code deleted or deferred deletion blocker recorded.
- [ ] Post-commit review found no unresolved worthwhile findings.
