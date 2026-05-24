# 018-036: MacOS Executable KB Closeout Research

Status: completed

## Proposal Context

- Source proposal: `docs/proposals/018-platform-executable-format-knowledge.md`
- Blocked by: `docs/issues/018-030-executable-kb-restart-and-state-sync.md`
- Purpose: perform the hard Mac executable-format research pass needed to close
  or formally defer the remaining Proposal 018 Mac blockers.
- This is research-first. It must not promote facts, change parser behavior, or
  mutate Mac target artifacts.

## Knowledge Delta

Produce a complete evidence packet for each remaining Mac executable-format
blocker:

- nonzero CODE byte-entry rule;
- classic 68K CODE relocation/fixup record location, encoding, affected
  offsets, and application rules;
- source-to-CODE fixture proof requirements;
- non-CODE resource payload semantics boundary, including whether only type-level
  facts are currently justified.

Each packet must end in one of:

- accepted-ready;
- parser-assertion-ready;
- candidate-only;
- deferred because local evidence is insufficient;
- unsupported/out of scope with reason.

Completed research packets:

| Blocker | Classification for 018-037 | Evidence found | Evidence not found |
| --- | --- | --- | --- |
| Nonzero CODE byte-entry rule, including `movea.l (a7)+,a0` | Deferred/candidate-only | Current KB packets and parser/listing output expose `macos.code_resource.movea_stack_a0.*` as candidate only. Inside Macintosh Volume III validates Segment Loader/CODE resource loading, A5/jump-table globals, and CODE 0 error handling. MPW `Asm` committed inventory observes CODE 1 and other nonzero CODE resources. | No committed Inside Macintosh or MPW source states that `movea.l (a7)+,a0` is the general nonzero CODE entry instruction, or gives a byte-level entry offset rule inside CODE payloads. |
| Classic 68K CODE relocation/fixup record location, encoding, affected offsets, and application rules | Deferred | Inside Macintosh Volume III confirms Segment Loader loading of CODE resources and runtime memory/A5 context. Current parser/report output emits `macos.segment_loader.relocation_fixups.deferred` with `deferred_only`. | No committed source identifies classic 68K CODE resource fixup records, their on-disk location, byte encoding, affected payload offsets, or Segment Loader application rules. Later PEF/CFM-style relocation material remains non-evidence for classic CODE. |
| Source-to-CODE fixture proof | Deferred fixture work | MPW manuals and Proposal 012 cite `Asm`, `Link`, and `Rez` build flow. Proposal 012/018 prior notes identify `Interfaces&Libraries/Interfaces/AStructMacs/Sample` as the preferred future fixture. `ext/macos_tools/mpw_gm/source.json` records only MPW tool executable metadata, and `asm_code_resources.json` inventories MPW/Tools/Asm CODE resources. | No committed built product for the candidate Sample source is captured or reproduced, and current Sample source must not be mapped to MPW/Tools/Asm CODE resources. |
| Non-CODE resource payload semantics | Mixed: CURS type-level accepted-ready/already accepted; payload decoding unsupported; other listed types candidate-only | Inside Macintosh Volume III defines Cursor data/mask/hotSpot shape, and MPW docs list CURS as a resource type. Current KB has `macos.resource_fork.curs.layout.accepted` for type-level rows only. | No current output contains per-resource CURS payload bytes or decoded bitmap/hotspot fields. No committed local evidence promotes `acur`, `cmdo`, or `vers` beyond candidate inventory for this executable KB slice. |

## Default Behavior

No default parser/listing/web behavior changes. Current Mac candidate/deferred
visibility must remain as-is.

## Evidence Standard

Use committed local sources first:

- Inside Macintosh markdown and metadata;
- MPW manuals and examples;
- extracted MPW-GM source/build/resource inventories;
- current `knowledge/platform_executable_formats.json`;
- current parser/listing/report output.

External or optional-local sources may be named as future work but must not be
treated as committed evidence.

## Implementation Slice

AFK research slice:

- search all committed Mac documentation and MPW-derived inventories for each
  blocker;
- record exact citations or absence-of-evidence findings;
- compare findings to current parser/listing output;
- identify whether 018-037 can promote, parser-assert, defer, or mark
  unsupported for each blocker;
- update Proposal 018 observations with the research result.

## Research Completion Standard

This issue is complete only if the worker can show a double-checked research
trail. A quick grep is insufficient. The result must include searched source
families, search terms or reviewed sections, positive evidence, negative
evidence, and second-pass review.

Research trail:

- Source families checked: `ext/docs_macos/Inside_Macintosh_*.md`,
  `ext/docs_macos/MPW_and_Assembly_Language_Programming_for_the_Macintosh_1987.md`,
  `ext/docs_macos/Programming_With_Macintosh_Programmers_Workshop_1987.md`,
  `ext/macos_tools/mpw_gm/source.json`,
  `ext/macos_tools/mpw_gm/asm_code_resources.json`,
  `knowledge/platform_executable_formats.json`, Proposal 012 closeout text, and
  current Mac parser/report/test surfaces in `src/platform_file_lib.c`,
  `src/platform_macos_resource.c`, `tests/test_platform_executable_formats.py`,
  and `tests/test_web_e2e_cdp.py`.
- First-pass terms included `movea`, `jump table`, `Segment Loader`, `CODE`,
  `relocation`, `fixup`, `A5`, `resource fork`, `CURS`, `acur`, `cmdo`, and
  `vers`.
- Second-pass terms included `byte_entry_rule`, `movea_stack_a0`,
  `relocation_fixups`, `candidate_only`, `deferred_only`, `source-to-CODE`,
  `Sample`, `Asm`, `Link`, `Rez`, and `non_code_metadata`.
- Positive evidence: committed sources support CODE resources, CODE 0
  jump-table metadata, nonzero CODE segment headers, MPW Link/Rez workflow,
  A5/jump-table offsets, and type-level CURS layout.
- Negative evidence: no committed source found a general nonzero CODE
  byte-entry instruction/rule, classic CODE fixup record format, or a
  source/build/product fixture that maps current Sample source to MPW/Tools/Asm
  CODE bytes.

## Completion Evidence

- `uv run python -m amiga_reversing.tools.platform_executable_formats validate`
  passed.
- `uv run python -m pytest tests/test_platform_executable_formats.py -q` passed.
- `uv run python -m pytest tests/test_validate_018_issues.py -q` passed.

## Research Coverage

- [x] Inside Macintosh committed markdown checked for CODE entry and fixups.
- [x] MPW manuals committed markdown checked for Link/CODE entry and fixups.
- [x] MPW-GM examples/build files checked for source-to-CODE evidence.
- [x] Current Mac executable KB records checked.
- [x] Current Mac parser/listing/report output checked against findings.
- [x] Second-pass search checked for missed byte-entry/fixup terminology.

## Research Review

- [x] Every blocker has a final research classification.
- [x] Accepted-ready facts cite committed evidence.
- [x] Parser-assertion-ready facts explain why direct parse/citation is
  insufficient and why the assertion is standard.
- [x] Deferred/unsupported facts identify exactly what evidence is missing.
- [x] No parser behavior, generated facts, or target artifacts were changed.

## Required Sign-Off

- [x] Proposal 018 records the research outcome.
- [x] 018-037 has enough information to resolve or formally defer each blocker.
- [x] Available 018 validation commands pass.
