# 030-006 Add Target OS Compatibility Summary

Status: Ready
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

The KB still has OS/API availability metadata, and recovered platform calls
still carry `available_since` and `fd_version`, but there is no target-level OS
compatibility summary. The rendered source emits a memory map header, while OS
compatibility is absent from both source headers and structured web/API output.

The old header should not be restored as a separate string path. The clean
replacement is one structured target platform summary consumed everywhere. This
issue also brings the existing memory map header under that same summary owner
so generated source headers have one implementation path.

## Scope

Refactor the Amiga OS runtime/source-analysis path so target OS compatibility
is first-class structured data, and create the target platform summary module
that owns generated header content.

Required changes:

- introduce a target platform summary data shape that includes memory map and
  OS compatibility
- move the current memory map header emission to render from that summary
- preserve raw function `available_since` text in generated runtime metadata
  where known
- add a raw version rank model for `1.0`, `1.1`, `1.2`, `1.3`, `2.0`, `2.04`,
  `2.1`, `3.0`, `3.1`, and `3.5`
- keep normalized compatibility enum only as a derived comparison aid
- preserve `fd_version` as interface/library version text
- aggregate observed recovered platform calls into one target summary
- represent `no_os_calls` and `unknown` states explicitly
- read expected target profile from explicit target metadata first; optionally
  use project/disk year only as an inferred, non-failing hint
- render the source OS compatibility header from that summary
- expose the same summary in listing summary/API payloads
- ensure source export includes the C-rendered header, not a Python duplicate

Expected source header shape:

```asm
; OS compatibility
;   minimum required: 3.1
;   observed API availability: 1.3, 2.0, 3.1
;   observed FD/interface versions: v34, v36, v38, v40
;   max requirement drivers:
;     utility.library/GetUniqueID at section_0+$000004D2 requires 3.1, fd v39
```

## Acceptance Criteria

- Existing memory map header output is rendered through the target platform
  summary path.
- A target with recovered Amiga OS calls exposes structured
  `os_compatibility` summary data.
- Rendered source emits an OS compatibility header adjacent to the memory map
  header.
- Web/API/export paths consume the same structured summary or rendered source
  output; none recompute compatibility independently.
- Raw availability precision is preserved when present in the parsed KB.
- Raw `1.2` and `3.0` availability values do not collapse to `1.3` or `3.1`
  in the target summary.
- Targets with no recovered OS calls report `status=no_os_calls` and no minimum
  OS requirement.
- Targets with recovered calls but no usable availability report
  `status=unknown` and no false minimum OS requirement.
- The maximum-required version lists the call(s) that force it.
- Unexpected-new API warnings name whether the expected profile came from
  explicit target metadata or inferred project/disk year.
- Existing enum-only availability use is replaced, not kept as a compatibility
  bridge.

## Non-Goals

- Reparse new NDK sources.
- Guess missing OS versions.
- Keep the old header implementation as a legacy fallback.
- Add UI-only compatibility logic.
- Fail checks based only on inferred project/disk-year expectations.

## Verification

```text
fixture target with no recovered OS calls
fixture target with recovered calls but unknown availability
fixture target with recovered calls across multiple available_since/fd versions
fixture target proving raw 1.2 and 3.0 survive target summary aggregation
source-header test proving memory map and OS compatibility both render from target platform summary
listing summary/API test proving structured os_compatibility is emitted
source export test proving exported source includes the C-rendered header
cmd /c src\precommit.bat
```
