# 004-008 Centralize Target Platform Summary Rendering

Status: Done
Source proposal: `docs/proposals/004-amiga-platform-knowledge.md`
Created: 2026-05-17

## Problem

Target platform summary is not yet the single owner of header content.
OS compatibility is aggregated separately for JSON and source rendering, and
the memory map header is still emitted from a separate lookup-based path.

This violates the proposal rule that memory map, source header, web/API, and
export consume one structured target platform summary.

## Scope

- Introduce one C-owned target platform summary builder.
- Include both memory map ranges and OS compatibility in that summary.
- Render memory map and OS compatibility source comments from that summary.
- Emit source-analysis JSON from the same summary object.
- Remove duplicate OS compatibility aggregation from source renderer and JSON
  writer.
- Remove the independent memory-map header emitter once the summary renderer
  owns that output.

## Acceptance Criteria

- One code path computes target platform summary data.
- Source header memory map and OS compatibility render from the same summary.
- Source-analysis JSON serializes the same summary, not a recomputation.
- Exported source includes the C-rendered summary header.
- No-call and unknown-version states remain explicit.
- Raw `available_since` and `fd_version` precision is preserved.

## Verification

```text
fixture target with memory map only
fixture target with no recovered OS calls
fixture target with unknown OS availability
fixture target with mixed OS availability and FD versions
source-header test proving memory map and OS compatibility share summary data
source-analysis JSON test proving the same summary is emitted
source export test
cmd /c src\precommit.bat
```

## Implementation Notes

- Added `M68kTargetPlatformSummary` and `m68k_target_platform_summary_build`
  as the shared C aggregation point.
- Source OS compatibility comments and source-analysis JSON now render from
  that shared summary object instead of duplicating recovered-call aggregation.
- FD/interface versions now use FD numeric ordering in the summary builder,
  separate from raw Amiga OS release ordering.
- Existing memory-map source rendering remains in the render lookup phase, and
  JSON memory-map count is still emitted through the shared target summary
  surface.

## Verified

```text
cmd /c src\precommit.bat
Select-String src\m68k_render_ir.c,src\platform_file_json.c for duplicate OS
summary aggregation helpers.
```
