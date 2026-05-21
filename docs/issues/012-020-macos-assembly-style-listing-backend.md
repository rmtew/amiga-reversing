Status: open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Render Mac OS CODE ranges through a Mac OS assembly-style listing path instead
of the raw Amiga listing path.

Problem:
The current Mac listing path wraps selected CODE bytes as a raw binary source.
The shared C backend then emits Amiga-style source, including
`SECTION code,code`. That is not acceptable for a Classic Mac OS target. The
source should be useful to someone reading Mac OS / MPW-style assembly, even
though byte-for-byte MPW roundtrip is out of scope.

What to build:
Add or generalize a listing backend so Mac CODE ranges render with Mac-oriented
source conventions, labels, comments, resource/segment provenance, and explicit
metadata/data spans. The solution should cleanly extend the shared framework
instead of adding a one-off string post-processor.

Acceptance criteria:
- Mac projects no longer route rendered CODE source through `amiga-raw`.
- Mac target source does not emit Amiga-specific directives such as
  `SECTION code,code`.
- Listing rows carry Mac resource/segment provenance: HFS path, fork,
  resource type/id/name, and classified range.
- Metadata/data spans from 012-019 render as data or comments, not instructions.
- The listing remains compatible with the normal web listing route and row
  locator model.
- Amiga and Atari ST listing output is unchanged unless a shared abstraction is
  intentionally improved with tests.

Required tests:
- Server/listing test asserting Mac listing output lacks `SECTION code,code`.
- Renderer/source text test for Mac-style segment/range headings.
- Web smoke test opening the Mac target and showing Mac CODE provenance with
  listing rows.
- Regression tests for existing Amiga raw/binary listing output.

Blocked by:
- 012-019 for classified Mac CODE ranges.
