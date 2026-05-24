# 020-001: Current Import Pipeline Inventory

Status: active
Type: AFK
Source proposal: docs/proposals/020-platform-executable-import-pipeline.md

## Proposal Context

- Source proposal: `docs/proposals/020-platform-executable-import-pipeline.md`
- Current state: 018/019 provide executable-format KB authority and parser-owned
  fact refs, but platform parser, import, listing, artifact, and verifier paths
  are not yet proven to flow through one shared executable model.
- Desired state after this issue: a checked replacement map identifies exactly
  which current paths 020 must preserve, migrate, or delete.

## What To Build

Create a concise implementation inventory for Amiga HUNK, Atari PRG, and Mac
CODE covering parser summaries, executable range classification, analysis
import, listing/rendering, target artifacts, verifier/coverage gates, and web/API
surfaces.

This is not a broad research sink. The output must be a replacement map that
lets later issues code against known boundaries.

## Acceptance Criteria

- [ ] Current Amiga HUNK parser-to-listing/import path is traced.
- [ ] Current Atari PRG parser-to-listing/import path is traced.
- [ ] Current Mac HFS/resource/CODE parser-to-listing/import path is traced.
- [ ] Existing tests and proof commands for each path are listed.
- [ ] Superseded path candidates are identified, with deletion blocked until a
  replacement issue proves coverage.
- [ ] Proposal 020 is updated with unexpected implementation constraints.
- [ ] No code behavior changes are made unless needed to expose a missing
  test/proof command.

## Blocked By

None - can start immediately.

## Required Sign-Off

- [ ] Proposal 020 read before work.
- [ ] 018 and 019 boundaries respected.
- [ ] Inventory is double-checked against source search, not only proposal text.
- [ ] Replacement map is actionable for 020-002 through 020-009.
- [ ] `git diff --check` passes.

## Completion Evidence

Record the replacement map, the searches used to verify it, and the exact next
implementation issue that should start first.
