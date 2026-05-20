Status: Implemented
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

Implementation notes:
- Added `src/scripts/generate_mac_os_runtime.py`, extracting only the
  allowlisted MPW AInclude records and observed baseline calls.
- Generated `src/generated/mac_os_runtime.c/.h` with cited source paths and
  line evidence, plus C lookup helpers for records, fields, calls, and OPWORD
  calls.
- `_PBHGetVInfoSync` records `A0` parameter-block input and `D0` OSErr result.
- `_NumToString` is a package macro with package word `$A9EE`; OPWORD lookup
  deliberately does not return it.
- `src/test_mac_os_runtime.c` consumes the generated C/H tables directly so
  baseline facts are not duplicated in hand-coded consumers.
- Actual Mac render annotation waits for the project/backend slice; this issue
  provides the generated runtime table the later render path should consume.

Verification:
- `uv run python -m pytest tests\test_macos_runtime_generation.py -q`
- `uv run ruff check src\scripts\generate_mac_os_runtime.py tests\test_macos_runtime_generation.py`
- `cmd /c src\build.bat`
- `src\build\m68k_c_unit_tests.exe`
