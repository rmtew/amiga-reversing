Status: blocked
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Render selected Classic Mac OS CODE resources as actual m68k listing rows in the
web UI.

Problem:
The current container view exposes a word preview for `CODE 1 Main`, while a
separate smoke test proves the bytes can pass through the existing raw m68k
listing backend. Completion requires the UI to show the real listing through
the normal listing model, with the resource/container metadata linked to it.

Acceptance criteria:
- `CODE 1 Main` is imported as a listing source/range through the shared listing
  framework.
- The web UI shows m68k listing rows, not just `dc.w` preview words.
- Container metadata links the listing back to resource type/id/name, fork,
  payload offset/size/hash, and unsupported Segment Loader state.
- The implementation extends shared listing/source abstractions where needed;
  it must not keep a Mac-only preview path as the accepted design.
- Unsupported relocation/fixup behavior remains explicit.

Required tests:
- C/backend listing test for selected CODE bytes.
- Server API listing payload test for the Mac CODE segment.
- Web smoke/e2e test showing CODE listing rows and container metadata together.
- Regression test for existing raw binary listing behavior.

Blocker recorded:
- The Python container smoke path can extract `CODE 1 Main` bytes, but the
  shared listing framework does not yet import a Mac CODE resource as a normal
  project listing source/range.
- Keeping the current word preview as the accepted UI listing would be a
  Mac-only side path. This issue remains blocked by the C-backed container path
  and shared listing/source schema work from 012-013 and 012-014.
