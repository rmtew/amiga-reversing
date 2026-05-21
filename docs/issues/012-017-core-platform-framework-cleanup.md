Status: reopened / incomplete
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Use Mac OS support to cleanly extend the shared platform framework rather than
adding side paths.

Problem:
Mac OS introduces source projects, fork/resource containers, and CODE segment
metadata that do not exactly match Amiga HUNK or Atari PRG. If the current
framework cannot express those concepts, the right fix is to generalize the
framework. A Mac-only workaround would create legacy code and tech debt.

Acceptance criteria:
- Any platform concept needed by Mac but also meaningful generally is represented
  in shared framework types or APIs.
- Mac-specific code is limited to actual Mac semantics: HFS/Finder metadata,
  resource fork/CODE conventions, MPW source/build semantics, and Mac OS facts.
- No compatibility branch exists only to preserve the prototype Python payload
  shape, `classic_macos` identifier, or helper API.
- If a clean framework extension is too large for the current slice, the blocker
  is recorded in this issue/proposal and implementation pauses at that boundary.
- Existing Amiga and Atari behavior remains supported through the generalized
  path, not through copied legacy branches.
- Mac listing/rendering does not masquerade as `amiga-raw`. If the shared
  framework lacks a Mac raw/CODE listing backend concept, add that abstraction
  or record the blocker instead of accepting Amiga output as Mac output.

Required tests:
- Shared project/source/container schema tests covering Amiga, Atari ST, and
  Mac OS examples.
- Regression tests proving existing Amiga/Atari imports still use the shared
  framework path.
- Review checklist confirming no Mac-only workaround path remains.

Previous partial result:
- The earlier blocker was removed by 012-013, 012-014, and 012-016: Mac HFS,
  fork/resource, CODE metadata, normal project payloads, and selected CODE
  listing rows now flow through C-backed import/listing support and the normal
  project/listing API.
- Review found no remaining `classic_macos` compatibility alias in Python/JS
  source or tests.
- Cleaned up the stale web source test contract that still expected
  `renderClassicMacProject(projectData)` and `generation: "macos_starter"`.
  The test now follows the normal listing-backed Mac render signature and
  asserts the old starter generation literal is absent.
- Remaining Mac-specific code is actual Mac semantics or thin wrappers over
  C-backed HFS/resource/CODE behavior. The committed example target remains
  separate 012-018 work.

Corrective review:
- The framework cleanup is not complete while the Mac listing path routes
  through raw Amiga-style assembly and emits `SECTION code,code`. 012-020 owns
  the Mac OS listing/backend abstraction needed to close this cleanly.

Verification:
- `uv run python -m pytest tests\test_web_app_source.py -q`
