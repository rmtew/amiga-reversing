Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Expose the Classic Mac OS starter project in the web UI with both source and
binary/container pivots.

Required pivots:

```text
source file
segment
routine
resource
trap/API fact
binary fork
CODE resource
unsupported state
```

Out of scope:
Do not build a polished Mac-specific IDE or emulator view. Do not require
round-trip support.

Files likely touched:
- web/API payloads
- web UI project/listing components
- target/project metadata serializers
- tests under `tests/`

Acceptance criteria:
- UI can open the `Sample` source project view and navigate file, segment,
  routine, resource, build, and API-fact structure.
- UI can open the `Asm` binary/container view and navigate data fork, resource
  fork, `CODE 0`, `CODE 1 Main`, and other CODE resources.
- UI clearly distinguishes source facts from observed binary facts.
- Unsupported Mac platform areas are visible and specific.
- Existing Amiga/Atari project views are not regressed.

Required tests:
- API payload test for Mac source project view.
- API payload test for Mac binary/container view.
- Web UI smoke test for both views.
- Regression smoke test for an existing non-Mac target.

Cleanup / deletion:
Delete after UI/API support is implemented and covered.

Notes for agents:
The goal is a useful starter view, not decoration. Prioritize dense, inspectable
structure and stable navigation.

Implementation notes:
- Added a Classic Mac OS starter web payload that combines the `Sample`
  source project/render model with the real MPW `Asm` binary/container import.
- Source pivots expose source files, segments, routines, resource
  declarations, build products, and Mac OS API/record facts.
- Binary/container pivots expose data/resource forks, Finder metadata,
  `CODE 0`, all `CODE` resources, selected `CODE 1 Main`, and the CODE 1
  listing preview.
- The payload explicitly records that `Sample` source segments do not map to
  observed `MPW/Tools/Asm` CODE resources.
- The web app now has a Classic Mac branch that renders the source pivots,
  binary/container pivots, source/binary boundary, and unsupported state when
  the API payload includes `classic_macos`.
- Existing disk and binary project branches remain in place; this slice does
  not add full Mac target lifecycle creation or round-trip support.

Verification:
- `uv run python -m pytest tests\test_macos_web_view.py tests\test_web_app_source.py -q`
- `uv run ruff check amiga_reversing\disasm\macos_web_view.py tests\test_macos_web_view.py tests\test_web_app_source.py`
- `uv run mypy amiga_reversing\disasm\macos_web_view.py tests\test_macos_web_view.py`
- `node --check amiga_reversing\web\app.js`
