# 018-036: MacOS Executable KB Closeout Research

Status: active

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

## Research Coverage

- [ ] Inside Macintosh committed markdown checked for CODE entry and fixups.
- [ ] MPW manuals committed markdown checked for Link/CODE entry and fixups.
- [ ] MPW-GM examples/build files checked for source-to-CODE evidence.
- [ ] Current Mac executable KB records checked.
- [ ] Current Mac parser/listing/report output checked against findings.
- [ ] Second-pass search checked for missed byte-entry/fixup terminology.

## Research Review

- [ ] Every blocker has a final research classification.
- [ ] Accepted-ready facts cite committed evidence.
- [ ] Parser-assertion-ready facts explain why direct parse/citation is
  insufficient and why the assertion is standard.
- [ ] Deferred/unsupported facts identify exactly what evidence is missing.
- [ ] No parser behavior, generated facts, or target artifacts were changed.

## Required Sign-Off

- [ ] Proposal 018 records the research outcome.
- [ ] 018-037 has enough information to resolve or formally defer each blocker.
- [ ] Available 018 validation commands pass.

