# Proposal 004: Amiga Platform Knowledge

## TODO Coverage

- `TODO.md` Knowledge Base: Amiga Platform.

## Current State

- `knowledge/adcd21_inventory.md` records parsed ADCD material: NDK 3.1, OS_CHANGES, IFF specs, and the Hardware Reference Manual.
- `src/scripts/kb/ndk_parser.py` already builds compatibility metadata from multiple NDK roots and OS_CHANGES.
- Hardware register extraction currently records 245 registers in `knowledge/amiga_hw_registers.json`; `knowledge/adcd21_inventory.md` says 104 have bit data.
- `knowledge/amiga_ndk_corrections.json` contains seeded corrections with `review_status` provenance.
- `knowledge/amiga_hunk_format.md` lists `HUNK_OVERLAY`, but there is no obvious primary-source parser/test coverage for overlay structure beyond symbol extraction.

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
