# Proposal 004: Amiga Platform Knowledge

## TODO Coverage

- `TODO.md` Knowledge Base: Amiga Platform.

## Current State

- `knowledge/adcd21_inventory.md` records parsed ADCD material: NDK 3.1, OS_CHANGES, IFF specs, and the Hardware Reference Manual.
- `src/scripts/kb/ndk_parser.py` already builds compatibility metadata from multiple NDK roots and OS_CHANGES.
- Hardware register extraction currently records 245 registers in `knowledge/amiga_hw_registers.json`; `knowledge/adcd21_inventory.md` says 104 have bit data.
- `knowledge/amiga_ndk_corrections.json` contains seeded corrections with `review_status` provenance.
- `knowledge/amiga_hunk_file.json` includes `HUNK_OVERLAY` as a valid load-file record id, but the normalized runtime metadata has no `record_types.HUNK_OVERLAY` entry.
- `knowledge/amiga_hunk_format.md` documents a `HUNK_OVERLAY` payload shape, but there is no obvious primary-source parser/test coverage for overlay structure beyond symbol extraction.
- `src/m68k_reproduction_compare.c` still hardcodes Amiga HUNK ids and skip logic instead of consuming `src/generated/amiga_hunk_file_runtime.*`.

## Current Codebase Evaluation

- NDK/include coverage is the strongest part of this proposal. `tests/test_parse_ndk.py` already covers include ownership, constants, value domains, compatibility versions, callback semantics, and sparse autodoc overlays.
- Hardware register extraction exists, but the parser still contains manual CIA bit tables and copy rules. That is acceptable as parser-owned knowledge only when every asserted block is cited clearly.
- Corrections provenance exists as data, but runtime generation consumes seeded and validated corrections the same way. There is no dedicated review command for `knowledge/amiga_ndk_corrections.json`.
- Include-backed symbol generation exists through `symbol_include_rows()` and vendored include scans. What is missing is a target-driven "these platform symbols were unresolved" report that points back to include families.
- HUNK overlay support is currently low-confidence. The enum exists, the valid-record list mentions it, and the old markdown gives a shape, but parser/runtime metadata and tests do not prove it.

## Near-Term Relevance

- High: platform metadata that improves current listing quality: hardware registers, OS calls, struct fields, value domains, and version-aware names.
- Medium: corrections review. It reduces trust debt before more seeded facts accumulate.
- Low now: broad ADCD expansion such as NDK 3.5, CD32, and Amiga Mail. Add only when a target demonstrates a gap.
- Low until evidence appears: `HUNK_OVERLAY` implementation. Keep it documented but do not let UI or reproduction depend on it yet.

## Simpler Rewrite Opportunities

1. Generate HUNK comparison helpers from platform format runtime metadata.
   - Files: `src/m68k_reproduction_compare.c`, `knowledge/amiga_hunk_file.json`, `src/scripts/generate_platform_format_runtime.py`.
   - Problem: reproduction comparison duplicates HUNK constants and record skip rules already represented in generated metadata.
   - Rewrite: move record-id lookup, relocation classification, section-record detection, and skippable payload shape behind generated helper tables.
   - Benefit: one platform format source of truth; less drift between loader, writer, and comparison.

2. Make `HUNK_OVERLAY` explicit or absent in normalized metadata.
   - Files: `knowledge/amiga_hunk_file.json`, `src/platform_amiga_hunk.c`, tests around HUNK parsing/reproduction.
   - Problem: `HUNK_OVERLAY` is listed as valid but has no normalized record type, so unknown-record skip behavior is doing implicit work.
   - Rewrite: either add a cited `record_types.HUNK_OVERLAY` with fixture tests, or remove it from valid record lists until primary-source layout is proven.
   - Benefit: no half-supported container shape.

3. Add a corrections review module before adding more corrections.
   - Files: `knowledge/amiga_ndk_corrections.json`, new CLI/tests.
   - Problem: review status is metadata only; generation does not enforce review workflow.
   - Rewrite: add a read-only listing command first, then an explicit promote action that preserves citation and review provenance.
   - Benefit: seeded facts remain useful without becoming invisible debt.

4. Add a platform KB coverage/report command.
   - Files: `src/scripts/kb/ndk_parser.py`, `src/scripts/generate_amiga_os_runtime.py`, `knowledge/adcd21_inventory.md`.
   - Problem: inventory is hand-maintained while generated KBs are large and hard to audit.
   - Rewrite: generate counts for sources, functions, constants, structs, fields, hardware registers, bitfields, value domains, and correction statuses.
   - Benefit: proposal progress becomes measurable and reviewable.

5. Make target-driven gaps the driver for include expansion.
   - Files: target usage/reproduction reporting and platform metadata catalogs.
   - Problem: broad include parsing risks adding low-value facts before targets need them.
   - Rewrite: report unresolved platform-looking symbols by owner/include family, then parse only those families.
   - Benefit: smaller work slices and better locality for tests.

## Clean Near-Term Work

1. Keep all Amiga platform facts parser-owned.
   - OS version refinements come from NDK roots, OS_CHANGES, or cited primary docs.
   - Hardware bit definitions come from the Hardware Reference Manual parser.
   - HUNK overlay facts come from ADCD or another vetted primary source.

2. Add a corrections review command.
   - List seeded corrections by file, symbol/function, source, and citation.
   - Promote `seeded` to `validated` only through an explicit review action.
   - Reject silent promotion during parse or generation.

3. Expand include-backed symbol coverage only when targets need it.
   - Start from unresolved hardware/platform symbols observed in target output.
   - Add parser support for the relevant include family.
   - Regenerate runtime tables and add focused rendering tests.

4. Verify `HUNK_OVERLAY` from primary source before implementation.
   - Document the exact record layout.
   - Add a minimal fixture from a vetted sample or a hand-built fixture whose bytes are cited against the source.
   - Add parser and listing tests before any UI or reproduction claims rely on overlays.

## Better Version

- Treat ADCD inventory as a live source map: parsed, candidate, deferred, and invalid sources are tracked explicitly.
- Generate a platform KB coverage report with counts for functions, constants, structs, fields, hardware registers, bitfields, and review statuses.
- Let target analysis report missing platform symbols by include family so parser work is driven by observed gaps.

## Larger Architecture Notes

- The KB should distinguish primary parsed facts, parser-asserted facts, seeded corrections, and validated corrections.
- Renderers and analyzers should consume generated tables only; they should not know whether a fact came from NDK, ADCD, or a correction file.
- Version-aware labels need stable version metadata in the KB, not target-specific naming rules.

## Verification

- Parser tests for OS version refinement and hardware bit extraction.
- Correction review tests proving seeded entries do not become validated automatically.
- HUNK overlay fixture tests once the primary layout is documented.
- Renderer tests for any newly added include-backed symbols.

## Review Sign-Off

Reviewed against `TODO.md` and current code on 2026-05-16. Scope is coherent as proposal work; no implementation is claimed here.
