Status: reopened / incomplete
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Render selected Classic Mac OS CODE resources as Mac OS m68k listing rows in the
web UI from classified executable ranges.

Problem:
The current container view exposes a word preview for `CODE 1 Main`, while a
separate smoke test proved bytes can pass through the existing raw m68k listing
backend. That is no longer sufficient. Review found the committed `asm.s` starts
with Amiga-style `SECTION code,code` and decodes Mac CODE metadata/data bytes as
instructions before the apparent real code. Completion requires the UI to show
Mac-style listing rows from classified CODE ranges, with the resource/container
metadata linked to them.

Acceptance criteria:
- `CODE 1 Main` is imported as one or more classified executable ranges through
  the shared listing framework.
- The web UI shows Mac OS m68k listing rows, not just `dc.w` preview words and
  not raw decoding of segment metadata/data bytes.
- The rendered listing does not emit Amiga-specific source directives such as
  `SECTION code,code`.
- The first rendered instructions are justified by CODE layout/entrypoint
  evidence. Obvious metadata/data prefix bytes are represented as data/metadata,
  not bogus `ori.b` instructions.
- Obvious orphaned code islands in the selected CODE resource are either
  rendered as additional ranges or recorded as deferred islands with evidence.
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

Previous partial result:
- Mac OS projects now expose the normal `/api/projects/<id>/listing/open` and
  `/api/projects/<id>/listing` routes.
- The listing builder extracts the selected nonzero `CODE` resource through the
  C-backed HFS/resource path and feeds those bytes into the shared raw m68k
  listing artifact path.
- The Mac project payload links the selected `CODE` segment back to the listing
  route, resource type/id/name, resource fork, code byte range, hashes, and
  unsupported Segment Loader state.
- The web Mac view renders a `CODE Listing` panel with actual listing rows from
  the shared listing API instead of accepting the old word preview as the
  listing surface.
- Relocation/fixups, complete Segment Loader behavior, source mapping, and
  byte-for-byte roundtrip remain explicit unsupported starter behavior.

Corrective requirement:
- The previous result is only route plumbing and a raw selected-slice smoke
  path. It must not be treated as completed CODE rendering until 012-019 and
  012-020 remove the metadata-as-code and Amiga-style renderer failures.

Verification:
- `uv run ruff check amiga_reversing\disasm\c_backend.py amiga_reversing\disasm\macos_listing_source.py amiga_reversing\disasm\macos_project_payload.py amiga_reversing\disasm\server.py tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_disasm_server.py tests\test_web_app_source.py`
- `uv run python -m pytest tests\test_macos_c_backend.py tests\test_macos_project_payload.py tests\test_disasm_server.py::test_route_macos_listing_returns_code_rows_from_shared_listing_cache tests\test_disasm_server.py::test_route_macos_listing_open_uses_macos_listing_builder tests\test_disasm_server.py::test_route_listing_anchor_code_returns_window_at_non_address_row tests\test_web_app_source.py::test_web_app_renders_macos_code_listing_from_listing_route -q`
