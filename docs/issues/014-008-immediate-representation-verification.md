Status: Open
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

Acceptance criteria:
- Operand identity is durable across listing rebuilds.
- Instruction immediates and data literals both render with the selected style.
- The loop verifier checks Manual Action Log, semantic reload, projected
  representation, rendered text, and round-trip exactness where output-affecting.

Remaining work:
- Add the action-specific reversing-loop verifier for representation commands.
- Add negative verifier tests that fail on missing Manual Action Log projection,
  missing rendered text, or failed round-trip.

Required tests:
Operand identity tests, instruction-immediate rendering tests, data literal
regression tests, and loop verifier tests.
