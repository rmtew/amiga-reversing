Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Make source render and analysis consume generated Classic Mac OS metadata
through the durable platform path.

Problem:
The starter render tests pass handcrafted Python dictionaries for Mac OS calls
and records. That was acceptable for proving the shape of the source view, but
it duplicates facts that are now generated into `src/generated/mac_os_runtime.*`.
Completion requires one source of truth.

Acceptance criteria:
- Source/project render input comes from generated Mac OS metadata or an API over
  that generated metadata.
- Tests do not duplicate call/record opwords, package words, register protocol,
  record sizes, or source citations in handcrafted dictionaries except as
  expected-output assertions.
- If Python needs metadata, it obtains it through a wrapper over generated/core
  metadata rather than maintaining a separate Python fact table.
- Missing metadata is represented as explicit unsupported/review debt, not
  patched in ad hoc for the render path.

Required tests:
- Render smoke tests using generated Mac OS metadata.
- Drift test showing generated metadata is current.
- Regression test that `_PBHGetVInfoSync` and `_NumToString` render from the
  generated metadata source.

Resolution:
- The Mac OS runtime generator now emits `src/generated/mac_os_runtime.json`
  beside the generated C/H files.
- `build_macos_source_project` loads the generated metadata by default and the
  renderer exposes the metadata source in its payload.
- Source render tests no longer carry a handcrafted call/record table; they
  assert `_PBHGetVInfoSync` and `_NumToString` facts from the generated source.
