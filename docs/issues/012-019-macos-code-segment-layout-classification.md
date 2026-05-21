Status: open
Source proposal: docs/proposals/012-classic-mac-os-m68k-platform.md

Scope:
Build the Mac CODE segment layout model needed before nonzero CODE resources
are rendered as executable source.

Problem:
The current C-backed selected CODE extraction treats nonzero CODE payloads as
flat code after a four-byte prefix. The committed `asm.s` shows why that is not
good enough: bytes before the apparent real code are decoded as `ori.b`
instructions, and later code/data islands are collapsed into a mostly linear
decode. For Mac OS target support, CODE resources need a segment-aware model
that can distinguish loader metadata, jump-table/runtime data, executable
islands, and unknown areas.

What to build:
Add a durable C-backed Mac CODE layout parser/classifier for MPW `Asm` CODE
resources. It should expose classified ranges to Python/API/listing consumers:
metadata, data, candidate code, confirmed code, entrypoints, orphaned code
islands, and deferred/unsupported spans with evidence.

Acceptance criteria:
- C APIs expose classified CODE resource ranges instead of only `payload + 4`
  selected bytes.
- `CODE 0` remains metadata-only.
- Nonzero CODE resources preserve segment header/jump-table metadata as
  metadata/data, not executable instructions.
- The apparent `CODE 1` executable entry that starts at `movea.l (a7)+,a0` is
  discovered or justified from layout/control-flow evidence.
- Obvious orphaned code islands are detected and represented as code candidates,
  confirmed code, or deferred spans with reason/evidence.
- Unknown layout areas are explicitly deferred with the missing context needed
  to resume. They are not decoded as code just to fill the listing.
- Existing HFS/resource summary metadata remains intact.

Required tests:
- C unit tests for synthetic CODE payloads with metadata prefix, code range, and
  data island.
- Fixture drift test proving MPW `Asm` CODE 1 no longer starts rendering at the
  metadata prefix.
- Python wrapper/API test for classified CODE range JSON.
- Regression test that unsupported or unknown spans are reported, not silently
  rendered as instructions.

Blocked by:
None - can start immediately.
