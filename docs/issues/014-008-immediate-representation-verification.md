Status: Complete
Source proposal: docs/proposals/014-source-converging-manual-action-surface.md

Scope:
Make immediate and data-literal representation changes genuinely
source-converging.

Current evidence:
- `ManualRepresentationMetadata` and `create_manual_representation` exist.
- Command catalog exposes representation commands on immediate and data literal
  elements.
- Existing focused tests prove data-literal append/projection, but not durable
  instruction-immediate rendering or an action-specific loop verifier.

Progress:
- Manual representation metadata now preserves `operand_index` for
  operand-scoped identities.
- C policy import/export preserves operand-indexed representations.
- Instruction immediates render selected hex/binary/character styles, and the
  assembler parser accepts binary (`%...`) and character (`'A'`) literals so
  rendered output round-trips exactly.
- Data-literal representation coverage remains intact.
- The reversing-loop verifier for representation commands checks Manual Action
  Log hash/count, semantic reload of the representation, rendered listing text,
  and exact round-trip.

Acceptance criteria:
- Operand identity is durable across listing rebuilds.
- Instruction immediates and data literals both render with the selected style.
- The loop verifier checks Manual Action Log, semantic reload, projected
  representation, rendered text, and round-trip exactness where output-affecting.

Required tests:
Operand identity tests, instruction-immediate rendering tests, data literal
regression tests, and loop verifier tests.

Completed evidence:
- `tests/test_manual_seed_effective_metadata.py`
- `tests/test_c_backend.py::test_real_dll_manual_representation_styles_classified_bytes_without_classifying`
- `tests/test_c_backend.py::test_real_dll_manual_representation_styles_instruction_immediates`
- `tests/test_reversing_loop.py` representation verifier tests

Follow-up boundary:
Per-element data-block layout, field breakdown, and treating values as
references without relocation require more than display representation; track
the investigation in `014-015-data-block-layout-and-reference-interpretation.md`
and implementation in `014-016` through `014-019`.
