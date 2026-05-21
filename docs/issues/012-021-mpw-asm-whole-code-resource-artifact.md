Status: implemented
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Make the committed MPW `Asm` target artifact cover the whole CODE-resource
shape, not only selected CODE 1.

Problem:
The current `asm.s` inventories all CODE resources but renders only `CODE 1`.
That reads like the Asm target is represented, while most executable resources
are only names and hashes. For a useful starter artifact, every CODE resource
must be accounted for as rendered source or as a structured, justified
placeholder. Partial coverage is allowed only when the artifact says it is
partial and records what evidence is missing.

What to build:
Regenerate `targets/macos_hfs_mpw_gm/targets/macos_file_mpw_tools_asm/asm.s`
so it covers every CODE resource from `MPW-GM/MPW/Tools/Asm`. Render classified
executable ranges where supported. Render unresolved resources/ranges as
structured placeholders with a reason, evidence, and next context needed.

Acceptance criteria:
- Every CODE resource in the resource fork appears in the artifact with
  coverage status: rendered, partial, deferred, metadata-only, or unsupported.
- Rendered CODE ranges use the Mac-style listing backend from 012-020.
- CODE resources with obvious code islands are not hidden behind a generic
  placeholder if the classifier can identify them.
- Deferred resources/ranges include concrete reasons, not vague "unsupported"
  labels.
- The artifact clearly distinguishes the container target, Asm file subtarget,
  resource fork, CODE resources, non-CODE resources, and source/project
  boundary.
- Drift tests fail if a CODE resource is missing from the rendered/deferred
  coverage table.
- The committed `asm.s` remains illustrative and useful without claiming MPW
  Asm/Link/Rez roundtrip.

Required tests:
- Artifact drift test checking CODE resource coverage count matches the C
  resource summary.
- Text regression test that the artifact does not contain the previous initial
  bogus `ori.b` metadata decode.
- Test that missing/unclassified CODE resources produce structured placeholders
  with reasons.

Blocked by:
- 012-019 for CODE layout/range classification.
- 012-020 for Mac-style listing output.

Implementation notes:
- The committed `asm.s` now includes a `CODE resource coverage` table with one
  structured row for every C-summary CODE resource.
- Coverage statuses are explicit:
  `metadata-only` for CODE 0, `rendered` for the selected CODE 1 listing,
  `partial` for resources with confirmed entry evidence but deferred
  full-resource expansion, and `deferred` for resources where the classifier
  lacks entry evidence.
- Partial/deferred rows include classifier layout kinds, entry evidence, and a
  concrete reason instead of hiding unrendered CODE resources behind name/hash
  inventory lines.
- The drift test now compares coverage row count against the C resource summary
  so a missing CODE resource fails the artifact test.

Verification:
- `uv run python -m pytest tests\test_macos_target_artifact.py -q`
- `uv run ruff check --fix tests\test_macos_target_artifact.py`

Follow-up:
- Full expansion of every confirmed CODE segment remains future work until
  relocation/source-boundary context is represented per segment. The starter
  artifact now records that limitation explicitly instead of implying complete
  rendered coverage.
