# 018-030: Executable KB Restart and State Sync

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Purpose: restart the live 018 issue trail after completed issue files were
  consolidated/deleted, and produce the current authoritative state map for
  overnight worker planning.
- This issue is docs-only. It must not change parser behavior, generated facts,
  target artifacts, or platform KB records.
- Downstream issues in this batch depend on this issue for a clean done/open/
  blocked map.

## Knowledge Delta

No executable-format KB facts were changed. This issue records the current 018
state from committed proposal text, `knowledge/platform_executable_formats.json`,
validator/report code, and tests.

Current Mac state:

- `macos.hfs_resource_fork.code_resources.mpw_application` is the only
  `kb_backed=true` executable-format record.
- Accepted/parser-consumable Mac facts currently include HFS resource-fork
  application code, CODE-resource acceptance, CODE 0 jump-table metadata,
  nonzero CODE segment headers, jump-table entries, below-A5 globals, Segment
  Loader CODE loading, MPW Link application output, runtime A5 jump-table
  offset, CODE 1 main startup/main segment entry, segment jump-table spans,
  renderer accepted-vs-candidate labeling, and type-level CURS layout.
- `movea.l (a7)+,a0` remains candidate-only through
  `macos.code_resource.movea_stack_a0.*`; it is not accepted byte-entry
  evidence.
- Classic 68K CODE relocation/fixup interpretation remains deferred through
  `macos.segment_loader.relocation_fixups.deferred` and the blocked
  implementation packet.
- Source-to-CODE proof remains a fixture strategy, not an accepted source map.
  The current accepted MPW evidence is not proof that the Sample source maps to
  the emitted CODE bytes.
- Non-CODE resource semantics are limited to type-level `CURS` layout. CURS
  payload-byte decoding is unsupported, and `acur`, `cmdo`, and `vers` remain
  candidate inventory.

Current Amiga/Atari state:

- `amiga.hunk.load_file.basic_backfill` is schema-valid but
  `kb_backed=false`. It contains parser-asserted accepted slice facts, but the
  record is still report-only and does not authorize migrated parser behavior.
- `atari_st.prg.gemdos_basic_backfill` is schema-valid but `kb_backed=false`.
  It also contains parser-asserted accepted slice facts while remaining
  report-only.
- 018-031 and 018-032 must decide the smallest justified accepted or
  parser-asserted KB-backed slice, or record formal candidate/deferred blockers.

Current generated-table and parser-coverage state:

- Generated platform executable C tables already exist and are freshness-tested
  against `knowledge/platform_executable_formats.json`; they must remain
  mechanical output from that KB, not a second source of truth.
- Parser fact reference validation already rejects citation-packet candidate ids
  and status/parser-use drift.
- 018-033 remains open because the generated consumer table must be refreshed
  after the next KB authority changes and must preserve fact id, platform,
  state, parser-use authority, and owning record.
- 018-034 remains open because parser-emitted facts still need one auditable
  coverage report over accepted, candidate, deferred, unsupported, and invalid
  claims.

Proposal 012 downstream state:

- Proposal 012 remains downstream of 018. It may consume 018 results, but it
  must not accept Mac byte-entry or CODE relocation/fixup heuristics itself.
- The 012 closeout blockers still owned by 018 are nonzero CODE byte-entry
  evidence and classic 68K CODE relocation/fixup evidence. Formal deferral is a
  valid 018 result if exact local evidence is not found.

Done/open/blocked matrix:

| Work item | State | Current authority | Next edge |
| --- | --- | --- | --- |
| 018-001 through 018-010 | Done, issue files consolidated into Proposal 018 | Schema, first Mac accepted record, guardrails, parser fact validation, Mac parser/listing migration, and multi-CODE visibility are recorded in Proposal 018 implementation notes. | Historical only; do not reopen from deleted issue files. |
| 018-011 through 018-016 | Done/consolidated or represented by current tests and KB state | Amiga/Atari report-only records, generated table freshness, Mac non-CODE/object/library research, and citation audit state are present in Proposal 018 notes/tests. | Current live replacements are 018-031, 018-032, 018-033, 018-036, and 018-037. |
| 018-017 through 018-029 | Done/consolidated into Proposal 018 | Mac preview/UI, relocation citation packet, source-to-CODE research, 012 closeout matrix, byte-entry blocker, relocation blocker, fixture strategy, and CURS semantic slice are recorded. | Their conclusions are inputs to 018-036/018-037/018-035. |
| 018-030 | Done by this file | Restart/state-sync only; no behavior or KB change. | Unblocks 018-031, 018-032, 018-033, 018-035, 018-036, and 012-023. |
| 018-031 | Open, blocked by 018-030 before start | Amiga HUNK record is currently report-only despite accepted slice facts. | May proceed after this commit; must not touch Mac parser/listing/web files. |
| 018-032 | Open, blocked by 018-030 before start | Atari ST PRG record is currently report-only despite accepted slice facts. | May proceed after this commit; must not touch Mac parser/listing/web files. |
| 018-036 | Open, blocked by 018-030 before start | Mac byte-entry, CODE fixup, source-to-CODE, and non-CODE boundaries need double-checked research packets. | May proceed after this commit; must not promote facts. |
| 018-037 | Open, blocked by 018-036 | No durable final state can be changed until 018-036 evidence packets exist. | Converts 018-036 outcomes into accepted/parser-asserted or formal deferred/unsupported KB state. |
| 018-033 | Open, blocked by 018-030; best after 018-031, 018-032, and 018-037 | Existing generated table is freshness-tested but must be the durable consumer surface after final KB state. | Start after Amiga/Atari and ideally Mac final-state work. |
| 018-034 | Open, blocked by 018-033 | Current parser reference validation is not the full coverage report. | Must report parser-emitted facts against generated KB metadata and fail closed on unknown accepted claims. |
| 018-035 | Open, blocked by 018-030; stronger after 018-034 and 018-037 | Current tests guard some candidate/deferred leakage, but not the final strongest surfaces. | Enforce Mac byte-entry/fixup blockers cannot leak as accepted. |
| 018-038 | Open, blocked by 018-031, 018-032, 018-034, 018-035, and 018-037 | Closeout must use current validation, not historical issue labels. | Promote durable conclusions into Proposal 018, then delete completed 018 issue files only after proposal state is durable. |
| 012-023 | Open downstream blocker map, blocked by 018-030 | Proposal 012 is downstream and still blocked on 018-owned Mac executable evidence. | May map downstream 012 work after this commit, but cannot bypass 018. |

No misleading proposal wording requiring immediate correction was found during
this sync. The main restart hazard is that Amiga/Atari records contain
accepted-looking parser-asserted fact ids while their records remain
`kb_backed=false`; workers must treat them as report-only until 018-031/018-032
resolve that boundary.

## Default Behavior

No runtime behavior changes. Current parser/listing/web behavior remains
unchanged.

## Evidence Standard

Used only committed proposal text, committed KB files, current validator output,
current parser/report code, and current tests. No new citations were invented
and no facts were promoted.

## Implementation Slice

Docs-only restart slice completed:

- reviewed Proposal 018 and Proposal 012 closeout text;
- reviewed `knowledge/platform_executable_formats.json`;
- reviewed `amiga_reversing.tools.platform_executable_formats`;
- reviewed current platform executable and 018 issue-validator tests;
- recorded the done/open/blocked matrix and exact dependency edges.

## Research Completion Standard

Completed with two passes:

- broad inventory pass over Proposal 018, Proposal 012, current 018 issues, KB
  validator/report output, and tests;
- contradiction pass over live issue dependencies, `kb_backed` state,
  candidate/deferred Mac facts, Amiga/Atari report-only records, generated-table
  freshness tests, and parser fact validation.

## Completion Evidence

- `uv run python -m pytest tests/test_validate_018_issues.py -q` passed.
- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passed.
- `uv run python -m amiga_reversing.tools.platform_executable_formats guardrails`
  reported one KB-backed record
  (`macos.hfs_resource_fork.code_resources.mpw_application`) and three
  report-only records (`macos.hfs_resource_fork.code_resources.thin_proof`,
  `amiga.hunk.load_file.basic_backfill`,
  `atari_st.prg.gemdos_basic_backfill`).

## Research Coverage

- [x] Proposal 018 status and relationship-to-012 sections checked.
- [x] Proposal 012 closeout matrix checked.
- [x] Platform executable KB file checked.
- [x] Platform executable validator/report code checked.
- [x] Relevant tests checked.
- [x] Second-pass contradiction review completed.

## Research Review

- [x] Findings distinguish accepted facts from candidate/deferred facts.
- [x] Findings distinguish live issue work from historical consolidated issue
  records.
- [x] No parser, target artifact, generated file, or web behavior was changed.
- [x] Dependency order for 018-031 through 018-035 and 012-023 was reviewed.

## Required Sign-Off

- [x] The issue records the authoritative current 018 state.
- [x] The issue identifies any proposal wording that would mislead a worker.
- [x] The worker ran the available issue/KB validation commands or recorded why
  they could not run.
