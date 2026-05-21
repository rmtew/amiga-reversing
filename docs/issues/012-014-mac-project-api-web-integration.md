Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Make Mac OS support reachable through the normal project, server API, and web
UI flow.

Problem:
The web renderer can display a helper-built `macos` payload, but the normal
server project payload does not emit durable Mac OS data. The starter view is
therefore fixture/helper-tested rather than openable as a real project in the
application.

This should be solved by extending the shared project/API/listing model. Do not
add a legacy Mac-only project payload path or a compatibility branch that
bypasses the normal project flow. If the current project model cannot express
source containers, fork/resource metadata, or selected CODE listings cleanly, fix
that model or raise the blocker.

Acceptance criteria:
- A Mac OS project record can be created or loaded from the committed MPW-GM
  fixture metadata.
- The normal project API emits `macos` data in the project payload.
- Existing prototype `classic_macos` naming is replaced, not supported through a
  compatibility alias.
- The API shape reuses or generalizes shared source/container/listing fields
  rather than inventing a parallel model where the core framework should be
  extended.
- The payload includes source view, binary container view, source/binary
  boundary, unsupported state, and provenance to the source image/fixtures.
- The web UI opens the Mac project through the same project route as other
  platforms and renders the source/container/listing view without test-only
  injection.
- No compatibility branch is retained only to support the Python prototype
  payload or the `classic_macos` identifier.
- Existing Amiga disk, Amiga binary, and Atari ST project views are not
  regressed.

Required tests:
- Server API payload test for a Mac project.
- Web app smoke/e2e test opening the Mac project through the normal route.
- Regression tests for existing Amiga/Atari project payload branches.
- Required-fixture gate or explicit skip report for environments missing the
  MPW-GM image/provider.

Result:
- Added first-class `ProjectKind.MACOS` records loaded from
  `macos_mpw_fixture` project origin metadata.
- The normal `/api/projects/<id>` route now emits `macos` payload data for
  ready Mac projects; no `classic_macos` compatibility alias is retained.
- The API payload includes source view, C-backed HFS/CODE binary container
  view, source/binary boundary, unsupported state, and provenance to the source
  image and committed source/resource/build metadata.
- The web renderer opens that payload through the existing project route via
  `projectData.macos`.
- Tests cover Mac project record loading, server route emission, web renderer
  source checks, and a committed MPW-GM fixture smoke through the C summary
  path.

Remaining follow-up:
- Actual selected CODE listing rows and a committed illustrative Mac target are
  still owned by 012-016 and 012-018, not by this API payload slice.
