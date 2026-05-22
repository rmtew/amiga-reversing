# 018-005: Mac OS Parser And Listing KB Migration

Status: completed

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

## Completion Evidence

- `src/platform_macos_resource.c` now reports validated fact ids for CODE 0 and
  nonzero CODE segment headers, candidate fact ids for the observed
  `movea.l (a7)+,a0` boundary, and deferred fact ids when entry evidence is
  missing.
- `src/platform_file_lib.c` exposes `kb_record_id`, `fact_id`, `fact_status`,
  and `parser_use` through the Mac C summary.
- Mac listing/project/artifact code renders the observed byte-entry range as
  `candidate_code`, not accepted `confirmed_code`, while preserving the MPW Asm
  starter listing path.
- `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s` was
  regenerated with candidate status/fact labels and no `SECTION code,code`.
- Proposal 012 was reassessed: parser/listing consumption landed, but exact
  byte-entry and relocation/fixup semantics remain deferred/candidate blockers.

Verification:

```text
cmd /c src\build.bat
uv run python -m amiga_reversing.disasm.macos_target_artifact --write
uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_asm_container.py tests\test_macos_project_payload.py tests\test_macos_target_artifact.py -q
```

## Research Coverage

- [x] Current Mac C resource/CODE parser checked.
- [x] Current Mac listing adapter checked.
- [x] Generated KB/check hook point checked.
- [x] Current heuristic code path checked.
- [x] Existing tests and artifact drift checks checked.
- [x] 012 closeout criteria checked.

## Research Review

- [x] Second pass checked trace blocks against named files/functions.
- [x] Candidate facts cannot produce accepted output.
- [x] Renderer wording reviewed for overclaiming.
- [x] Proposal 012 updated with evidence-backed status.

## Required Sign-Off

- [x] Proposal context checked before implementation.
- [x] 018-003 accepted Mac KB facts consumed or validated.
- [x] 018-004 guardrails pass.
- [x] Mac parser/listing tests pass.
- [x] Existing Amiga/Atari tests remain unaffected or changes are justified.
- [x] Stale heuristic code deleted or deferred deletion blocker recorded.
- [x] Post-commit review found no unresolved worthwhile findings.
