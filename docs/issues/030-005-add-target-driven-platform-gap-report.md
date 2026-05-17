# 030-005 Add Target-Driven Platform Gap Report

Status: Ready
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

Future platform KB expansion should be driven by target evidence. Today there
is no report that groups unresolved platform-looking values by likely owner or
include family.

## Scope

Add a target-level platform gap report.

The report should identify unresolved or weakly rendered platform-looking
values such as:

- custom chip address-range references
- CIA address-range references
- OS library LVO-shaped references
- constants that resemble known include families
- absolute values currently rendered generically but likely owned by platform KB

The first version can be conservative. False negatives are acceptable. False
positives should be explainable and grouped as candidates, not facts.

## Acceptance Criteria

- A command can report platform-looking gaps for a selected target.
- Output groups candidates by likely owner/source family.
- The report references the source artifact or parser area that would close the
  gap when known.
- Fixture coverage proves each reported candidate class.
- The report does not promote candidates into KB facts.

## Non-Goals

- Parse new include families.
- Automatically create corrections.
- Treat candidate matches as authoritative symbols.

## Verification

```text
target platform gap report command on a fixture target
focused platform gap report tests
cmd /c src\precommit.bat
```
