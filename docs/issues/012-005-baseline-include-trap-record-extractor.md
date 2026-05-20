Status: Open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Extract a narrow, cited Classic Mac OS metadata set from MPW AIncludes for
baseline rendering and analysis.

Initial records:

```text
Point
Rect
EventRecord
HVolumeParam
QDGlobals
WindowRecord
DCtlEntry
SysEnvRec
```

Initial calls/traps are only those observed in `Sample`, `Memory`, and `Count`.

Out of scope:
Do not ingest the entire Universal Interfaces tree, create a complete Toolbox
database, or hardcode trap facts directly in consumers.

Files likely touched:
- `knowledge/mac_os.json`
- new extractor/generator under `src/scripts/`
- `src/generated/mac_os_*.c/.h`
- tests under `tests/`

Acceptance criteria:
- Extracted records include field names, offsets, sizes, source include path,
  and source line evidence.
- Extracted trap/call facts include name, OPWORD when present, family/source
  include path, prototype text when present, and source line evidence.
- `_PBHGetVInfoSync` records A0 parameter-block input and D0 OSErr result.
- `_NumToString` is represented as a package macro emitting `$A9EE`, not a
  simple OPWORD alias.
- Generated C/H tables are consumed by render/analysis code, not duplicated as
  hardcoded constants.

Required tests:
- Record extraction tests for `Rect`, `EventRecord`, and `HVolumeParam`.
- Trap extraction tests for `_GetResource`, `_WaitNextEvent`, `_UnloadSeg`, and
  `_PBHGetVInfoSync`.
- Generated metadata drift check.

Cleanup / deletion:
Delete after extractor/generator work is implemented and covered.

Notes for agents:
Prefer a small, explicit allowlist of baseline-used facts. Bigger extraction
should be a later issue.
